import asyncio
import functools
import logging
import errno
import pyfuse3
import eons
from libtruckeefs import *
import os
import stat
import pyfuse3.asyncio  # Enables asyncio support in pyfuse3
from pathlib import Path

######## START CONTENT ########



def FuseMethod(func):
	@functools.wraps(func)
	async def wrapper(*args, **kwargs):
		# For logging: show method name, arguments, etc.
		logging.debug(
			f"Operation {func.__name__}("
			+ ", ".join([str(x) for x in args[1:]])
			+ (", " if kwargs else "")
			+ ", ".join([f"{k}={v}" for k, v in kwargs.items()])
			+ ")"
		)

		try:
			ret = await func(*args, **kwargs)
			logging.debug(f"Operation {func.__name__} returning {ret}")
			return ret

		# If the underlying code already raised pyfuse3.FUSEError,
		# just let it propagate so we keep the correct errno.
		except pyfuse3.FUSEError:
			logging.debug("Re-raising existing pyfuse3.FUSEError", exc_info=True)
			raise

		# For local I/O exceptions, we can map the .errno if present
		except (IOError, OSError, TruckeeFSInodeException) as e:
			logging.debug("Failed operation", exc_info=True)
			if hasattr(e, 'errno') and isinstance(e.errno, int):
				raise pyfuse3.FUSEError(e.errno)
			# Default to EACCES if no more specific errno is known
			raise pyfuse3.FUSEError(errno.EACCES) from e

		# Anything else is an unexpected exception => EIO
		except Exception as ex:
			logging.warning("Unexpected exception", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO) from ex

	return wrapper



pyfuse3.asyncio.enable()


def buildEntryAttributes(inodeId: int, inodeKind: str, info: dict) -> pyfuse3.EntryAttributes:
	attr = pyfuse3.EntryAttributes()
	attr.st_ino = inodeId
	attr.entry_timeout = 5  # directory entry cache timeout
	attr.attr_timeout = 5   # inode attribute cache timeout
	attr.generation = 0

	mode = info.get('mode', 0)
	if (inodeKind == "Directory"):
		mode |= stat.S_IFDIR
	elif (inodeKind == "File"):
		mode |= stat.S_IFREG
	attr.st_mode = mode

	attr.st_nlink = 1  # Link count
	attr.st_uid = info.get('uid', 0)
	attr.st_gid = info.get('gid', 0)
	attr.st_size = info.get('size', 0) if inodeKind == "File" else 0

	# Convert to nanoseconds
	attr.st_atime_ns = int(info.get('atime', 0) * 1e9)
	attr.st_mtime_ns = int(info.get('mtime', 0) * 1e9)
	attr.st_ctime_ns = int(info.get('ctime', 0) * 1e9)
	return attr


class TRUCKEEFS(RiverFS, pyfuse3.Operations):
	# pyfuse3.Operations flags, per the newer spec:
	supports_dot_lookup = True
	enable_writeback_cache = True
	enable_acl = False

	def __init__(this, name="TruckeeFS"):
		super().__init__(name)
		pyfuse3.Operations.__init__(this)

		this.arg.kw.required.append("mount")
		this.rootId = 1

		# Next file-handle counter (for both files and directories).
		this.nextFileHandle = 0
		# Maps file handles (ints) -> Inode objects
		this.openFiles = {}
		# Maps directory handles (ints) -> Directory objects
		this.openDirectories = {}

		this.arg.kw.optional["mount_options"] = "fsname=TruckeeFS,default_permissions,allow_other"

	def AllocateFileHandle(this):
		fh = this.nextFileHandle
		this.nextFileHandle += 1
		return fh

	###########################################################################
	# Helpers for getting/putting inodes, used by FUSE ops
	###########################################################################

	async def GetInode(this, inode: int) -> Inode:
		if (inode == 0):
			inode = this.rootId
		try:
			return await Inode.FromId(this, inode)
		except (TruckeeFSInodeException, FileNotFoundError):
			raise pyfuse3.FUSEError(errno.ENOENT)
		except Exception as e:
			logging.error(f"Unexpected error in GetInode({inode}): {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	async def GetOrRaiseENOENT(this, upath: str) -> Inode:
		try:
			return await Inode.From(this, upath, createIfNotExists=False)
		except TruckeeFSInodeException:
			raise pyfuse3.FUSEError(errno.ENOENT)

	async def GetOpenFile(this, fh: int) -> Inode:
		fileObj = this.openFiles.get(fh, None)
		if (fileObj is None):
			return None

		# Return the Inode object for the file
		# This prevents cached data from being held by the openFiles dict
		return await Inode.FromId(this, fileObj.id)

	async def GetOpenDirectory(this, fh: int) -> Inode:
		dirObj = this.openDirectories.get(fh, None)
		if (dirObj is None):
			return None

		# Return the Inode object for the directory
		# This prevents cached data from being held by the openDirectories dict
		return await Inode.FromId(this, dirObj.id)

	###########################################################################
	# Required pyfuse3.Operations methods in doc order
	###########################################################################

	# access(inode, mode, ctx) -> bool
	@FuseMethod
	async def access(this, inode, mode, ctx):
		obj = await this.GetInode(inode)
		# For now, do a naive check or simply "always allow"
		# If you want real permission checks, do them in obj.Access(mode)
		try:
			await obj.Access(mode)
			return True
		except IOError as e:
			raise pyfuse3.FUSEError(e.errno if hasattr(e, 'errno') else errno.EACCES)

	# create(parent_inode, name, mode, flags, ctx) -> (fi, attr)
	@FuseMethod
	async def create(this, parent_inode, name, mode, flags, ctx):
		parentObj = await this.GetInode(parent_inode)
		if (parentObj.kind != "Directory"):
			raise pyfuse3.FUSEError(errno.ENOTDIR)

		childName = name.decode('utf-8')
		childUpath = f"{parentObj.upath}/{childName}" if parentObj.upath else childName

		try:
			# Create a file
			fileObj = await File.From(this, childUpath, createIfNotExists=True)
			await fileObj.Save(mutated=True)
			# Set the requested mode
			await fileObj.Chmod(mode)

			# Now open and track it
			await fileObj.Open(flags)
			fh = this.AllocateFileHandle()
			this.openFiles[fh] = fileObj

			# Build attributes
			attr = await this.getattr(fileObj.id, ctx)

			fi = pyfuse3.FileInfo()
			fi.fh = fh
			# The spec says return (fi, attr).
			return fi, attr

		except Exception as e:
			logging.error(f"create error: {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	# flush(fh)
	@FuseMethod
	async def flush(this, fh):
		fileObj = await this.GetOpenFile(fh)
		if (fileObj is None):
			raise pyfuse3.FUSEError(errno.EBADF)

		# Forward to our Inode logic
		try:
			await fileObj.Flush()
		except Exception as e:
			logging.error(f"flush error on {fileObl.StringId()} (fh {fh}): {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	# forget(inode_list)
	# Must not raise any FUSEError (the kernel doesn't wait).
	async def forget(this, inode_list):
		# Decrease lookups. We do not strictly track reference counts in the example.
		# if (you need to do that, you can do so here):
		# for (ino, nlookup) in inode_list:
		#	 ...
		pass

	# fsync(fh, datasync)
	@FuseMethod
	async def fsync(this, fh, datasync):
		fileObj = await this.GetOpenFile(fh)
		if (fileObj is None):
			raise pyfuse3.FUSEError(errno.EBADF)
		# For now, just do a flush (we do not differentiate metadata vs data)
		try:
			await fileObj.Flush()
		except Exception as e:
			logging.error(f"fsync error on {fileObl.StringId()} (fh {fh}): {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	# fsyncdir(fh, datasync)
	@FuseMethod
	async def fsyncdir(this, fh, datasync):
		# We do not have specific caching for directories. No-op is fine.
		return

	# getattr(inode, ctx) -> EntryAttributes
	@FuseMethod
	async def getattr(this, inode, ctx=None) -> pyfuse3.EntryAttributes:
		obj = await this.GetInode(inode)
		info = await obj.GetAttr()
		return buildEntryAttributes(inode, obj.kind, info)

	# getxattr(inode, name, ctx)
	@FuseMethod
	async def getxattr(this, inode, name, ctx):
		# If you store xattrs in your Inode, you can retrieve them here.
		# Otherwise, raise ENOATTR if absent.
		obj = await this.GetInode(inode)
		xname = name.decode('utf-8') if isinstance(name, bytes) else name
		val = await obj.GetXAttr(xname)
		if (val is None):
			raise pyfuse3.FUSEError(errno.ENODATA)  # ENOATTR
		return val

	# init()
	def init(this):
		logging.info("TRUCKEEFS filesystem initialized (pyfuse3.Operations spec).")

	# link(inode, new_parent_inode, new_name, ctx)
	@FuseMethod
	async def link(this, inode, new_parent_inode, new_name, ctx):
		# Hard links not implemented in the example
		raise pyfuse3.FUSEError(errno.ENOSYS)

	# listxattr(inode, ctx)
	@FuseMethod
	async def listxattr(this, inode, ctx):
		obj = await this.GetInode(inode)
		xattrs = await obj.ListXAttr()
		# Return them as a list of byte strings
		return [x.encode('utf-8') for x in xattrs]

	# lookup(parent_inode, name, ctx) -> EntryAttributes
	@FuseMethod
	async def lookup(this, parent_inode, name, ctx):
		parentObj = await this.GetInode(parent_inode)
		if (parentObj.kind != "Directory"):
			raise pyfuse3.FUSEError(errno.ENOTDIR)

		childName = name.decode('utf-8')
		childUpath = f"{parentObj.upath}/{childName}" if parentObj.upath else childName

		childObj = await this.GetOrRaiseENOENT(childUpath)
		return await this.getattr(childObj.id, ctx)

	# mkdir(parent_inode, name, mode, ctx) -> EntryAttributes
	@FuseMethod
	async def mkdir(this, parent_inode, name, mode, ctx):
		parentObj = await this.GetInode(parent_inode)
		if (parentObj.kind != "Directory"):
			raise pyfuse3.FUSEError(errno.ENOTDIR)

		dirName = name.decode('utf-8')
		newUpath = f"{parentObj.upath}/{dirName}" if parentObj.upath else dirName

		try:
			dirObj = await Directory.From(this, newUpath, createIfNotExists=True)
			await dirObj.Save(mutated=True)
			await dirObj.Chmod(mode)
			return await this.getattr(dirObj.id, ctx)
		except Exception as e:
			logging.error(f"mkdir error: {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	# mknod(parent_inode, name, mode, rdev, ctx) -> EntryAttributes
	@FuseMethod
	async def mknod(this, parent_inode, name, mode, rdev, ctx):
		# Usually for creating special files (block/char devices, etc.)
		raise pyfuse3.FUSEError(errno.ENOSYS)

	# open(inode, flags, ctx) -> FileInfo
	@FuseMethod
	async def open(this, inode, flags, ctx):
		obj = await this.GetInode(inode)
		if (obj.kind != "File"):
			raise pyfuse3.FUSEError(errno.EISDIR)

		await obj.Open(flags)
		fh = this.AllocateFileHandle()
		this.openFiles[fh] = obj

		fi = pyfuse3.FileInfo()
		fi.fh = fh
		return fi

	# opendir(inode, ctx) -> fh
	@FuseMethod
	async def opendir(this, inode, ctx):
		dirObj = await this.GetInode(inode)
		if (dirObj.kind != "Directory"):
			raise pyfuse3.FUSEError(errno.ENOTDIR)

		fh = this.AllocateFileHandle()
		this.openDirectories[fh] = dirObj
		return fh

	# read(fh, off, size)
	@FuseMethod
	async def read(this, fh, off, size):
		fileObj = await this.GetOpenFile(fh)
		if (fileObj is None or fileObj.kind != "File"):
			raise pyfuse3.FUSEError(errno.EBADF)

		try:
			data = await fileObj.Read(off, size)
			return data
		except Exception as e:
			logging.error(f"read error on {fileObl.StringId()} (fh {fh}): {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	# readdir(fh, start_id, token)
	@FuseMethod
	async def readdir(this, fh, start_id, token):
		dirObj = await this.GetOpenDirectory(fh)
		if (dirObj is None or dirObj.kind != "Directory"):
			raise pyfuse3.FUSEError(errno.EBADF)

		# Get children
		entries = await dirObj.List()
		all_entries = ['.', '..'] + [entry.name for entry in entries]

		for idx, nameStr in enumerate(all_entries[start_id:], start=start_id):
			next_id = idx + 1

			if (nameStr == '.'):
				childInode = dirObj.id
			elif (nameStr == '..'):
				if (dirObj.id == this.rootId):
					childInode = dirObj.id
				else:
					parent = await dirObj.GetParent()
					childInode = parent.id
			else:
				childUpath = f"{dirObj.upath}/{nameStr}" if dirObj.upath else nameStr
				try:
					childObj = await Inode.From(this, childUpath, createIfNotExists=False)
					childInode = childObj.id
				except TruckeeFSInodeException:
					logging.warning(f"Skipping '{nameStr}' because it does not exist.")
					continue

			try:
				childAttr = await this.getattr(childInode)
				success = pyfuse3.readdir_reply(token, nameStr.encode('utf-8'), childAttr, next_id)
				if (not success):
					break
			except pyfuse3.FUSEError as e:
				logging.warning(f"Skipping entry {nameStr} due to error: {e}")
				continue

	# readlink(inode, ctx)
	@FuseMethod
	async def readlink(this, inode, ctx):
		# Symlinks not implemented in the example
		raise pyfuse3.FUSEError(errno.ENOSYS)

	# release(fh)
	@FuseMethod
	async def release(this, fh):
		fileObj = await this.GetOpenFile(fh)
		if (fileObj is None):
			return

		try:
			await fileObj.Close()
		except Exception as e:
			logging.error(f"release error on {fileObl.StringId()} (fh {fh}): {e}", exc_info=True)

		this.openFiles.pop(fh, None)

	# releasedir(fh)
	@FuseMethod
	async def releasedir(this, fh):
		dirObj = await this.GetOpenDirectory(fh)
		if (dirObj is None):
			return

		try:
			await dirObj.Close()
		except Exception as e:
			logging.error(f"releasedir error on {fileObl.StringId()} (fh {fh}): {e}", exc_info=True)

		this.openDirectories.pop(fh, None)

	# removexattr(inode, name, ctx)
	@FuseMethod
	async def removexattr(this, inode, name, ctx):
		obj = await this.GetInode(inode)
		xname = name.decode('utf-8') if isinstance(name, bytes) else name

		success = await obj.RemoveXAttr(xname)
		if (not success):
			raise pyfuse3.FUSEError(errno.ENODATA)

	# rename(parent_inode_old, name_old, parent_inode_new, name_new, flags, ctx)
	@FuseMethod
	async def rename(this, parent_inode_old, name_old, parent_inode_new, name_new, flags, ctx):
		pOldObj = await this.GetInode(parent_inode_old)
		pNewObj = await this.GetInode(parent_inode_new)
		if (pOldObj.kind != "Directory" or pNewObj.kind != "Directory"):
			raise pyfuse3.FUSEError(errno.ENOTDIR)

		oldName = name_old.decode('utf-8')
		newName = name_new.decode('utf-8')
		oldUpath = f"{pOldObj.upath}/{oldName}" if pOldObj.upath else oldName
		newUpath = f"{pNewObj.upath}/{newName}" if pNewObj.upath else newName

		try:
			obj = await Inode.From(this, oldUpath, createIfNotExists=False)
			await obj.Move(newUpath)
		except TruckeeFSInodeException:
			raise pyfuse3.FUSEError(errno.ENOENT)
		except Exception as e:
			logging.error(f"rename error on {oldUpath}: {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	# rmdir(parent_inode, name, ctx)
	@FuseMethod
	async def rmdir(this, parent_inode, name, ctx):
		parentObj = await this.GetInode(parent_inode)
		if (parentObj.kind != "Directory"):
			raise pyfuse3.FUSEError(errno.ENOTDIR)

		dirName = name.decode('utf-8')
		dirUpath = f"{parentObj.upath}/{dirName}" if parentObj.upath else dirName

		try:
			dirObj = await Inode.From(this, dirUpath, createIfNotExists=False)
			if (dirObj.kind != "Directory"):
				raise pyfuse3.FUSEError(errno.ENOTDIR)

			children = await dirObj.List()
			if (children):
				raise pyfuse3.FUSEError(errno.ENOTEMPTY)

			await dirObj.Unlink()
		except TruckeeFSInodeException:
			raise pyfuse3.FUSEError(errno.ENOENT)
		except Exception as e:
			logging.error(f"rmdir error on {dirUpath}: {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	# setattr(inode, attr, fields, fh, ctx)
	@FuseMethod
	async def setattr(this, inode, attr, fields, fh, ctx):
		# This is invoked on chmod, chown, truncate, utimens, etc.
		# fields is a pyfuse3.SetattrFields specifying which attributes changed.
		# You can handle them individually using fields.update_* booleans.
		#
		# If fh is not None, it means the file was opened with open().
		# If fh is None, it was path-based (like chmod(2)).
		#
		obj = None
		if (fh is not None):
			# might be file or directory
			obj = this.openFiles.get(fh) or this.openDirectories.get(fh)
		if (obj is None):
			obj = await this.GetInode(inode)

		try:
			if (fields.update_mode):
				await obj.Chmod(attr.st_mode)
			if (fields.update_uid):
				await obj.Chown(attr.st_uid, obj.meta['gid'])
			if (fields.update_gid):
				await obj.Chown(obj.meta['uid'], attr.st_gid)
			if (fields.update_size):
				if (obj.kind != "File"):
					raise pyfuse3.FUSEError(errno.EISDIR)
				size = attr.st_size
				await obj.Truncate(size)
			if (fields.update_atime or fields.update_mtime):
				# If your Inode class provides an interface for
				# setting times individually, call that.
				# E.g. await obj.Utime(...)
				# For simplicity, we just do:
				if (fields.update_atime):
					obj.meta['atime'] = attr.st_atime_ns / 1e9
				if (fields.update_mtime):
					obj.meta['mtime'] = attr.st_mtime_ns / 1e9
				await obj.Save(mutated=False)

			info = await obj.GetAttr()
			return buildEntryAttributes(obj.id, obj.kind, info)
		except pyfuse3.FUSEError:
			raise
		except Exception as e:
			logging.error(f"setattr error on inode {inode}: {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	# setxattr(inode, name, value, ctx)
	@FuseMethod
	async def setxattr(this, inode, name, value, ctx):
		obj = await this.GetInode(inode)
		xname = name.decode('utf-8') if isinstance(name, bytes) else name
		xval = value if isinstance(value, bytes) else value.encode('utf-8')
		try:
			await obj.SetXAttr(xname, xval)
		except Exception:
			raise pyfuse3.FUSEError(errno.EIO)

	# stacktrace()
	def stacktrace(this):
		# The spec says default is to log the current stacktrace. We'll just do so.
		import traceback
		logging.warning("fuse_stacktrace was triggered; printing stacktrace on all threads.")
		traceback.print_stack()

	# statfs(ctx)
	@FuseMethod
	async def statfs(this, ctx):
		# Provide filesystem usage info to commands like `df`.
		st = pyfuse3.StatvfsData()
		st.f_bsize = 4096
		st.f_frsize = 4096
		st.f_blocks = 1000000
		st.f_bfree = 500000
		st.f_bavail = 400000
		st.f_files = 1000000
		st.f_ffree = 500000
		st.f_favail = 500000
		st.f_namemax = 255
		return st

	# symlink(parent_inode, name, target, ctx)
	@FuseMethod
	async def symlink(this, parent_inode, name, target, ctx):
		# not implemented in the example
		raise pyfuse3.FUSEError(errno.ENOSYS)

	# unlink(parent_inode, name, ctx)
	@FuseMethod
	async def unlink(this, parent_inode, name, ctx):
		parentObj = await this.GetInode(parent_inode)
		if (parentObj.kind != "Directory"):
			raise pyfuse3.FUSEError(errno.ENOTDIR)

		fileName = name.decode('utf-8')
		fileUpath = f"{parentObj.upath}/{fileName}" if parentObj.upath else fileName

		try:
			fileObj = await Inode.From(this, fileUpath, createIfNotExists=False)
			await fileObj.Unlink()
		except TruckeeFSInodeException:
			raise pyfuse3.FUSEError(errno.ENOENT)
		except Exception as e:
			logging.error(f"unlink error on {fileUpath}: {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	# write(fh, off, buf)
	@FuseMethod
	async def write(this, fh, off, buf):
		fileObj = await this.GetOpenFile(fh)
		if (fileObj is None or fileObj.kind != "File"):
			raise pyfuse3.FUSEError(errno.EBADF)
		try:
			bytes_written = await fileObj.Write(off, buf)
			return bytes_written
		except Exception as e:
			logging.error(f"write error on {fileObl.StringId()} (fh {fh}): {e}", exc_info=True)
			raise pyfuse3.FUSEError(errno.EIO)

	###########################################################################
	# Overriding init/destroy from RiverFS / FUSE
	###########################################################################

	# Called by pyfuse3 when unmounting
	async def destroy(this):
		logging.info("Unmounting TruckeeFS.")
		# Clean up if needed

	###########################################################################
	# The main “Function” from eons.Functor, plus mounting
	###########################################################################

	async def RunFuse(this):
		options = set(this.mount_options.split(","))
		pyfuse3.init(this, this.mount, options)
		try:
			await pyfuse3.main()
		finally:
			pyfuse3.close()

	def Function(this):
		super().Function()
		# Make sure the root directory is present
		rootObj = this.Async(Inode.From(this, ""))
		this.rootId = rootObj.id

		logging.info(f"Mounting {this.name} at {this.mount}")

		if (this.eventLoop is None):
			logging.error("RiverFS event loop is not initialized!")
			raise RuntimeError("TRUCKEEFS cannot start without a valid event loop.")

		try:
			future = asyncio.run_coroutine_threadsafe(this.RunFuse(), this.eventLoop)
			future.result()  # Blocks until pyfuse3.main() completes
		except Exception as e:
			logging.error(f"Error running TruckeeFS FUSE main loop: {e}", exc_info=True)

