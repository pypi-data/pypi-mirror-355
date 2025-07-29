import eons
import asyncio
import os
import time
import platform
import sys
import sqlalchemy
import logging
from libtruckeefs import *
from sqlalchemy import select
from sqlalchemy import delete # make our lives easier
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
import redis
from enum import Enum
import json
import zlib
import struct
import errno
import multiprocessing
import threading
from pathlib import Path
import socket
import psutil
import aiohttp
from urllib.parse import quote
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
import enum
import re
from shutil import copy2
import aiofiles
import aiofiles.os
import sqlalchemy as sql
import sqlalchemy.orm as orm
import hashlib
import gzip
import shutil
import tempfile
import base64
from cryptography.fernet import Fernet
import subprocess
from eot import EOT

######## START CONTENT ########


class Test(eons.Functor):
	def __init__(this, name="Test"):
		super().__init__(name)

		this.arg.kw.optional["failure_is_fatal"] = True

		this.test = eons.util.DotDict()
		this.test.passed = True

	def Assert(this, condition, message):
		if (not condition):
			if (this.failure_is_fatal):
				raise AssertionError(message)
			else:
				logging.error(f"Assertion failed: {message}")
				this.test.passed = False

	def Async(this, coro):
		return this.executor.Async(coro)

	def BeforeFunction(this):
		this.test.start_time = time.time()
		logging.info(f"---- Starting test: {this.name} ----")

	def Function(this):
		this.Async(this.Run())

	def AfterFunction(this):
		this.test.end_time = time.time()
		logging.info(f"---- Finished test: {this.name} ----")
		logging.info(f"---- Test duration: {this.test.end_time - this.test.start_time} seconds ----")
		logging.info(f"---- Test result: {'PASSED' if this.test.passed else 'FAILED'} ----")

	async def Run(this):
		pass


# NOTE: ALL COMPATIBILITY TESTS MUST BE SYNCHRONOUS!
class CompatibilityTest(Test):
	def __init__(this, name="CompatibilityTest"):
		super().__init__(name)


class TestPlatform(CompatibilityTest):
	def __init__(this, name="Platform"):
		super().__init__(name)
	
	async def Run(this):
		this.Assert(platform.system().lower() == "linux", "Platform is not Linux")

class TestPythonVersion(CompatibilityTest):
	def __init__(this, name="PythonVersion"):
		super().__init__(name)
	
	async def Run(this):
		this.Assert(sys.version_info >= (3,9), "Python version is not 3.9 or greater")


class IntegrationTest(Test):
	def __init__(this, name="IntegrationTest"):
		super().__init__(name)


class TestTahoeConnection(IntegrationTest):
	def __init__(this, name="TahoeConnection"):
		super().__init__(name)
	
	async def Run(this):
		logging.info(f"Creating test TahoeConnection...")
		tahoe = this.executor.GetSourceConnection()
		this.Assert(tahoe is not None, "TahoeConnection not created")

		logging.info(f"Checking that rootcap exists...")
		response = await tahoe.Head(this.executor.rootcap, iscap=True)
		this.Assert(response.status == 200, "Rootcap does not exist")


class TestEphemeral(IntegrationTest):
	def __init__(this, name="Ephemeral"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Creating test Inode...")
		inode = Inode("test", "test")
		inode.id = 0
		inode.executor = this.executor

		logging.info(f"Setting ephemeral value...")
		await inode.SetEphemeral("test", True)

		logging.info(f"Retrieving ephemeral value...")
		value = await inode.GetEphemeral("test", coerceType=bool)
		logging.info(f"Ephemeral value: {value} ({type(value)})")
		this.Assert(value == True, "Ephemeral value does not match")

		logging.info(f"Deleting ephemeral value...")
		await inode.SetEphemeral("test", None)

		logging.info(f"Retrieving ephemeral value...")
		value = await inode.GetEphemeral("test")
		logging.info(f"Ephemeral value: {value} ({type(value)})")
		this.Assert(value is None, "Ephemeral value found")


class FunctionalTest(IntegrationTest):
	def __init__(this, name="FunctionalTest"):
		super().__init__(name)
	
		this.test.file = eons.util.DotDict()
		this.test.file.name = "__TESTFILE__.test"
		this.test.file.content = b"Hello, World!"

		this.test.directory = eons.util.DotDict()
		this.test.directory.name = "__TEST_DIRECTORY__"
		this.test.directory.subdirectory = "__TEST_SUBDIRECTORY__"


# NOTE: This will make the subsequent root inode id 2, which may break other implementations (e.g. fuse)
class TestInodeModel(FunctionalTest):
	def __init__(this, name="InodeModel"):
		super().__init__(name)
	
	async def Run(this):
		session = this.executor.GetDatabaseSession()

		logging.info(f"Checking if our test Inode already exists...")
		query = await session.execute(select(InodeModel).where(InodeModel.upath == "test"))
		inode = query.scalar()
		if (inode is not None):
			logging.info(f"Deleting existing test target...")
			await session.delete(inode)
			await session.commit()


		logging.info(f"Creating test InodeModel...")
		inode = InodeModel()
		inode.upath = "test"
		inode.name = "test"
		inode.kind = "test"
		inode.last_accessed = time.time()
		inode.data = "test"
		inode.pending_sync = False
		inode.pending_creation = False
		inode.pending_deletion = False

		logging.info(f"Adding InodeModel to database...")
		session.add(inode)
		await session.commit()

		logging.info(f"Retrieving InodeModel from database...")
		query = await session.execute(select(InodeModel).where(InodeModel.upath == "test"))
		inode = query.scalar()
		this.Assert(inode is not None, "InodeModel not found in database")

		logging.info(f"Deleting InodeModel from database...")
		await session.delete(inode)
		await session.commit()

		logging.info(f"Retrieving InodeModel from database...")
		query = await session.execute(select(InodeModel).where(InodeModel.upath == "test"))
		inode = query.scalar()
		this.Assert(inode is None, "InodeModel found in database")

		await session.close()


class TestFileCreation(FunctionalTest):
	def __init__(this, name="FileCreation"):
		super().__init__(name)
	
	async def Run(this):
		logging.info(f"Creating test file...")
		file = await File.From(this.executor, this.test.file.name, createIfNotExists=True)
		this.Assert(file is not None, "File not created")

		if (await file.IsStateLocked('sync')):
			timeout = 300
			while (timeout > 0):
				syncState = await file.GetState('sync')
				if (syncState == ProcessState.COMPLETE):
					break
				if (syncState == ProcessState.ERROR):
					raise Exception("File sync failed")
				timeout -= 1
				await asyncio.sleep(1)

			this.Assert(timeout > 0, "File sync timed out")

			writeState = await file.GetState('write')
			this.Assert(writeState == ProcessState.COMPLETE, "File write failed")

		else:
			logging.warning(f"File already exists. Will not try to create.")


class TestFileWrite(FunctionalTest):
	def __init__(this, name="FileWrite"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Opening test file...")
		file = await File.From(this.executor, this.test.file.name)

		logging.info(f"Writing data to file...")
		bytes_written = await file.Write(0, this.test.file.content)
		logging.info(f"Bytes written: {bytes_written}")
		this.Assert(bytes_written == len(this.test.file.content), "Bytes written does not match data length")

		timeout = 300
		while (timeout > 0):
			syncState = await file.GetState('sync')
			if (syncState == ProcessState.COMPLETE):
				break
			if (syncState == ProcessState.ERROR):
				raise Exception("File sync failed")
			timeout -= 1
			await asyncio.sleep(1)

		this.Assert(timeout > 0, "File sync timed out")

		writeState = await file.GetState('write')
		this.Assert(writeState == ProcessState.COMPLETE, "File write failed")


class TestFileRead(FunctionalTest):
	def __init__(this, name="FileRead"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Opening test file...")
		file = await File.From(this.executor, this.test.file.name)

		logging.info(f"Reading file data...")
		data = await file.Read(0, len(this.test.file.content))
		logging.info(f"Data read: {data}")
		this.Assert(data == this.test.file.content, "Data read does not match data written")


class TestFileDeletion(FunctionalTest):
	def __init__(this, name="FileDeletion"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Creating test file...")
		file = await File.From(this.executor, this.test.file.name)

		logging.info(f"Deleting test file...")
		await file.Unlink()

		timeout = 300
		while (timeout > 0):
			try:
				syncState = await file.GetState('sync')
			except FileNotFoundError:
				break
			except TruckeeFSInodeException:
				break
			if (syncState == ProcessState.COMPLETE):
				break
			if (syncState == ProcessState.ERROR):
				raise Exception("File sync failed")
			timeout -= 1
			await asyncio.sleep(1)

		this.Assert(timeout > 0, "File sync timed out")

		logging.info(f"Retrieving file from database...")
		session = this.executor.GetDatabaseSession()
		query = await session.execute(select(InodeModel).where(InodeModel.upath == this.test.file.name))
		file = query.scalar()
		this.Assert(file is None, "File found in database")

		await session.close()


class TestDirectoryCreation(FunctionalTest):
	def __init__(this, name="DirectoryCreation"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Creating test directory...")
		directory = await Directory.From(this.executor, this.test.directory.name, createIfNotExists=True)
		this.Assert(directory is not None, "Directory not created")

		if (await directory.IsStateLocked('sync')):
			timeout = 300
			while (timeout > 0):
				syncState = await directory.GetState('sync')
				if (syncState == ProcessState.COMPLETE):
					break
				if (syncState == ProcessState.ERROR):
					raise Exception("Directory sync failed")
				timeout -= 1
				await asyncio.sleep(1)

			this.Assert(timeout > 0, "Directory sync timed out")

			writeState = await directory.GetState('write')
			this.Assert(writeState == ProcessState.COMPLETE, "Directory creation failed")
		else:
			logging.warning(f"Directory already exists. Will not try to create.")


class TestSubdirectoryCreation(FunctionalTest):
	def __init__(this, name="SubdirectoryCreation"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Creating test directory...")
		directory = await Directory.From(this.executor, this.test.directory.name, createIfNotExists=True)
		this.Assert(directory is not None, "Directory not created")

		logging.info(f"Creating subdirectory...")
		subdirectory = await Directory.From(this.executor, f"{this.test.directory.name}/{this.test.directory.subdirectory}", createIfNotExists=True)
		this.Assert(subdirectory is not None, "Sub-Directory not created")

		if (await subdirectory.IsStateLocked('sync')):
			timeout = 300
			while (timeout > 0):
				syncState = await subdirectory.GetState('sync')
				if (syncState == ProcessState.COMPLETE):
					break
				if (syncState == ProcessState.ERROR):
					raise Exception("Sub-Directory sync failed")
				timeout -= 1
				await asyncio.sleep(1)

			this.Assert(timeout > 0, "Sub-Directory sync timed out")

			writeState = await subdirectory.GetState('write')
			this.Assert(writeState == ProcessState.COMPLETE, "Sub-Directory creation failed")
		else:
			logging.warning(f"Sub-Directory already exists. Will not try to create.")


class TestDirectoryDeletion(FunctionalTest):
	def __init__(this, name="DirectoryDeletion"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Creating test directory...")
		directory = await Directory.From(this.executor, this.test.directory.name)

		logging.info(f"Deleting test directory...")
		await directory.Unlink()

		await directory.WaitForStateBesides('sync', ProcessState.COMPLETE) # From previous tests

		timeout = 300
		while (timeout > 0):
			try:
				syncState = await directory.GetState('sync')
			except FileNotFoundError:
				break
			except TruckeeFSInodeException:
				break
			if (syncState == ProcessState.COMPLETE):
				break
			if (syncState == ProcessState.ERROR):
				raise Exception("Directory sync failed")
			timeout -= 1
			await asyncio.sleep(1)

		this.Assert(timeout > 0, "Directory sync timed out")

		logging.info(f"Retrieving directory from database...")
		session = this.executor.GetDatabaseSession()
		query = await session.execute(select(InodeModel).where(InodeModel.upath == this.test.directory.name))
		directory = query.scalar()
		this.Assert(directory is None, "Directory found in database")
		await session.close()

		# At some point, the gabrbage collector should run and remove the subdirectory.
		this.Assert(this.executor.process.garbage is not None, "Garbage daemon not running")
		timeout = 100
		while (timeout > 0):
			try:
				subdirectory = await Directory.From(this.executor, f"{this.test.directory.name}/{this.test.directory.subdirectory}")
				await subdirectory.GetState('delete') # will log state
			except FileNotFoundError:
				break
			except TruckeeFSInodeException:
				break

			timeout -= 1
			await asyncio.sleep(3) # this test takes a little longer since we have to wait for the garbage collector to run
		
		this.Assert(timeout > 0, "Sub-Directory not deleted")


class TestDirectoryListing(FunctionalTest):
	def __init__(this, name="DirectoryListing"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Creating test directory...")
		directory = await Directory.From(this.executor, this.test.directory.name, createIfNotExists=True)

		logging.info(f"Listing directory contents...")
		contents = await directory.List()
		logging.info(f"Directory contents: {contents}")

		logging.info(f"Creating subdirectory...")
		subdirectory = await Directory.From(this.executor, f"{this.test.directory.name}/{this.test.directory.subdirectory}", createIfNotExists=True)
		
		# Let's grab the directory again, since our cache is likely out of date now.
		directory = await Directory.From(this.executor, this.test.directory.name, createIfNotExists=False)
		contents = [c.name for c in await directory.List()]
		logging.info(f"Directory contents: {contents}")
		this.Assert(len(contents) >= 1 and this.test.directory.subdirectory in contents, "Subdirectory not found in listing")


class TestFileMove(FunctionalTest):
	def __init__(this, name="FileMove"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Creating test file...")
		file = await File.From(this.executor, this.test.file.name, createIfNotExists=True)
		fileId = file.id

		await file.Write(0, this.test.file.content)

		logging.info(f"Creating target directory...")
		directory = await Directory.From(this.executor, this.test.directory.name, createIfNotExists=True)

		# Remove the file if it already exists (e.g. from a previous run of future tests)
		targetContents = await directory.List()
		logging.debug(f"Target directory contents: {targetContents}")
		if (this.test.file.name in targetContents):
			logging.info(f"Removing existing file from target directory...")
			targetFile = await File.From(this.executor, f"{this.test.directory.name}/{this.test.file.name}")
			await targetFile.Unlink()
			timeout = 300
			while (timeout > 0):
				try:
					syncState = await targetFile.GetState('delete')
				except FileNotFoundError:
					break
				except TruckeeFSInodeException:
					break
				if (syncState == ProcessState.COMPLETE):
					break
				if (syncState == ProcessState.ERROR):
					raise Exception("File deletion failed")
				timeout -= 1
				await asyncio.sleep(1)
				# Now the file should be gone from the directory listing and from the cache.

		logging.info(f"Moving file to target directory...")
		file = await file.Move(f"{this.test.directory.name}/{this.test.file.name}")
		this.Assert(file is not None, "Destination file not found after move")
		this.Assert(file.upath == f"{this.test.directory.name}/{this.test.file.name}", "File upath does not match destination")

		try:
			sourceFile = await File.From(this.executor, this.test.file.name)
			if (sourceFile is not None and sourceFile.pending.delete):
				timeout = 300
				while (timeout > 0):
					try:
						syncState = await sourceFile.GetState('delete')
					except FileNotFoundError:
						break
					except TruckeeFSInodeException:
						break
					if (syncState == ProcessState.COMPLETE):
						break
					if (syncState == ProcessState.ERROR):
						raise Exception("Source file deletion failed")
					timeout -= 1
					await asyncio.sleep(1)
					# Now the file should be gone from the directory listing and from the cache.
			
			sourceFile = await File.From(this.executor, this.test.file.name)
			logging.error(f"After move, source file is: {sourceFile}")
			this.Assert(False, "Source file found after move")
		except FileNotFoundError:
			pass
		except TruckeeFSInodeException:
			pass
		logging.info(f"Source file not found after move, as expected.")

		#re-fetch the file just to make sure we have the latest data
		file = await File.From(this.executor, f"{this.test.directory.name}/{this.test.file.name}")
		fileContents = await file.Read(0, len(this.test.file.content))
		this.Assert(fileContents == this.test.file.content, "File contents do not match")


class TestFileCopy(FunctionalTest):
	def __init__(this, name="FileCopy"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Creating target directory...")
		directory = await Directory.From(this.executor, this.test.directory.name, createIfNotExists=True)

		# Remove the file if it already exists (e.g. from the previous test)
		targetContents = await directory.List()
		logging.debug(f"Target directory contents: {targetContents}")
		if (this.test.file.name in targetContents):
			logging.info(f"Removing existing file from target directory...")
			targetFile = await File.From(this.executor, f"{this.test.directory.name}/{this.test.file.name}")
			await targetFile.Unlink()
			timeout = 300
			while (timeout > 0):
				try:
					syncState = await targetFile.GetState('delete')
				except FileNotFoundError:
					break
				except TruckeeFSInodeException:
					break
				if (syncState == ProcessState.COMPLETE):
					break
				if (syncState == ProcessState.ERROR):
					raise Exception("File deletion failed")
				timeout -= 1
				await asyncio.sleep(1)
				# Now the file should be gone from the directory listing and from the cache.

		logging.info(f"Creating test file...")
		file = await File.From(this.executor, this.test.file.name, createIfNotExists=True)
		fileId = file.id

		logging.info(f"Copying file to target directory...")
		copiedFile = await file.Copy(f"{this.test.directory.name}/{this.test.file.name}")

		logging.info(f"Retrieving copied file from database...")
		session = this.executor.GetDatabaseSession()

		query = await session.execute(select(InodeModel).where(InodeModel.upath == f"{this.test.directory.name}/{this.test.file.name}"))
		file = query.scalar()
		this.Assert(file is not None, "File not found in database")
		this.Assert(file.id != fileId, "File id matches original file")

		query = await session.execute(select(InodeModel).where(InodeModel.id == fileId))
		file = query.scalar()
		this.Assert(file is not None, "Original file not found in database")

		await session.close()


class TestFileLifecycle(FunctionalTest):
	def __init__(this, name="FileLifecycle"):
		super().__init__(name)

	async def Run(this):
		logging.info(f"Creating test file...")
		file = await File.From(this.executor, this.test.file.name, createIfNotExists=True)

		logging.info(f"Writing data to file...")
		bytes_written = await file.Write(0, this.test.file.content)
		logging.info(f"Bytes written: {bytes_written}")
		this.Assert(bytes_written == len(this.test.file.content), "Bytes written does not match data length")

		logging.info(f"Waiting for file to enter pending upload state...")
		timeout = 10
		while (timeout > 0):
			pendingUpload = await file.GetEphemeral('pending_upload', coerceType=bool)
			if (pendingUpload):
				break

			timeout -= 1
			await asyncio.sleep(1)

		this.Assert(timeout > 0, "File upload timed out")

		logging.info(f"Waiting for file to sync upstream...")
		timeout = 300
		while (timeout > 0):
			syncState = await file.GetState('sync')
			if (syncState == ProcessState.COMPLETE):
				break
			if (syncState == ProcessState.ERROR):
				raise Exception("File sync failed")
			timeout -= 1
			await asyncio.sleep(1)
		
		this.Assert(timeout > 0, "File sync timed out")

		logging.info(f"Confirming file sync is complete...")
		timeout = 10
		while (timeout > 0):
			pendingUpload = await file.GetEphemeral('pending_upload', coerceType=bool)
			if (not pendingUpload):
				break

			timeout -= 1
			await asyncio.sleep(1)

		this.Assert(timeout > 0, "File upload flag not cleared")

		logging.info(f"Deleting cached file...")
		fileToDelete = str(file.data.path)
		# NOTE: this emulates the CachePruneDaemon
		await this.executor.PurgeCachedInode(file)
		session = this.executor.GetDatabaseSession()
		query = await session.execute(select(InodeModel).where(InodeModel.id == file.id))
		model = query.scalar()
		model.data = None
		await session.commit()
		await session.close()
		os.remove(fileToDelete)

		# Recreate the file
		file = await File.From(this.executor, this.test.file.name)

		# File download might be really quick, so let's see if it's here already.
		if (await file.IsStateLocked('sync')):
			timeout = 300
			while (timeout > 0):
				syncState = await file.GetState('sync')
				if (syncState == ProcessState.COMPLETE):
					break
				if (syncState == ProcessState.ERROR):
					raise Exception("File sync failed")
				timeout -= 1
				await asyncio.sleep(1)

			this.Assert(timeout > 0, "File sync timed out")

			writeState = await file.GetState('write')
			this.Assert(writeState == ProcessState.COMPLETE, "File write failed")

		logging.info(f"Confirming file sync is complete...")
		timeout = 10
		while (timeout > 0):
			pendingDownload = await file.GetEphemeral('pending_download', coerceType=bool)
			if (not pendingDownload):
				break

			timeout -= 1
			await asyncio.sleep(1)

		this.Assert(timeout > 0, "File download flag not cleared")

		logging.info(f"Reading file data...")
		file = await File.From(this.executor, this.test.file.name) # Re-fetch the file
		data = await file.Read(0, len(this.test.file.content))
		this.Assert(data == this.test.file.content, "Data read does not match data written")


class NegativeTest(FunctionalTest):
	def __init__(this, name="NegativeTest"):
		super().__init__(name)


class TestInvalidPathFileCreation(NegativeTest):
    def __init__(this, name="InvalidPathFileCreation"):
        super().__init__(name)

    async def Run(this):
        invalid_path = "some\0invalid\path"  # e.g. embed a null byte or other invalid chars
        try:
            file = await File.From(this.executor, invalid_path, createIfNotExists=True)
            this.Assert(False, "Expected exception on invalid path creation.")
        except Exception as e:
            logging.info(f"Caught expected exception: {e}")
            this.Assert(True, "Caught expected exception.")


class TestOpenNonExistentFile(NegativeTest):
    def __init__(this, name="OpenNonExistentFile"):
        super().__init__(name)

    async def Run(this):
        non_existent_path = "this_file_shouldnt_exist.test"
        try:
            file = await File.From(this.executor, non_existent_path, createIfNotExists=False)
            this.Assert(False, "Expected exception reading non-existent file.")
        except TruckeeFSInodeException as e:
            logging.info(f"Caught expected exception: {e}")
            this.Assert(True, "Raised the correct exception for non-existent file.")


class TestReadOnDirectory(NegativeTest):
    def __init__(this, name="ReadOnDirectory"):
        super().__init__(name)

    async def Run(this):
        dir_path = "__DIR_READ_NEGATIVE_TEST__"
        directory = await Directory.From(this.executor, dir_path, createIfNotExists=True)
        try:
            data = await directory.Read(0, 100)
            this.Assert(False, "Expected an exception reading from a directory.")
        except AttributeError as e:
            # Could also check for a more specialized error from your library
            logging.info(f"Caught expected error reading from directory: {e}")
            this.Assert(True, "Caught expected exception.")


class TestWriteOnDirectory(NegativeTest):
    def __init__(this, name="WriteOnDirectory"):
        super().__init__(name)

    async def Run(this):
        dir_path = "__DIR_WRITE_NEGATIVE_TEST__"
        directory = await Directory.From(this.executor, dir_path, createIfNotExists=True)
        try:
            await directory.Write(0, b"Something")
            this.Assert(False, "Expected an exception writing to a directory.")
        except AttributeError as e:
            logging.info(f"Caught expected error writing to directory: {e}")
            this.Assert(True, "Caught expected exception.")


class TestDeleteRootDirectory(NegativeTest):
    def __init__(this, name="DeleteRootDirectory"):
        super().__init__(name)

    async def Run(this):
        # Typically, your root directory upath is "", per your code
        try:
            root_dir = await Directory.From(this.executor, "", createIfNotExists=False)
            await root_dir.Unlink()
            this.Assert(False, "Expected an exception deleting the root directory.")
        except IOError as e:
            logging.info(f"Caught expected exception while deleting root dir: {e}")
            this.Assert(True, "Caught expected exception.")


class TestMoveFileOverDirectory(NegativeTest):
    def __init__(this, name="MoveFileOverDirectory"):
        super().__init__(name)

    async def Run(this):
        directory = await Directory.From(this.executor, "__MOVE_FILE_OVER_DIR__", createIfNotExists=True)
        file = await File.From(this.executor, "__MOVE_FILE_OVER_DIR__.test", createIfNotExists=True)

        try:
            await file.Move("__MOVE_FILE_OVER_DIR__")
            this.Assert(False, "Expected error when moving a file over a directory path.")
        except IOError as e:
            logging.info(f"Caught expected exception: {e}")
            this.Assert(True, "Caught expected exception.")




# Processes are some possible conflicting file operations. RiverFS uses 3 distinct processes to manage concurrent inode operations: Reads, Writes, and Syncs.
# Each process has a state, which can be one of the following:
class ProcessState(Enum):
	ERROR = 0
	PENDING = 1
	RUNNING = 2
	COMPLETE = 3
	IDLE = 4

	def __str__(self):
		return self.name

# The River Delta tracks what has been changed on the local / cache filesystem compared to the remote.
# It is backed by a remote database for persistence and scalability.
# NOTE: This class assumes that it is the authority on what the remote state should be.
#   If there are changes on the remote, this class WILL NOT resolve the conflict & the behavior of the resulting filesystem will be undefined.
#   Likely, *this will simply clobber the remote changes.
#
# RiverFS uses 3 distinct processes to manage concurrent inode operations: Reads, Writes, and Syncs.
# Reading and writing these semaphores needs to be fast, so we use Redis, instead of mysql.
# To query one of these semaphores, use GetState(), below.
# To set one of these semaphores, use SetState(), below.
#
class RiverDelta(eons.Functor):
	def __init__(this, name="River Delta"):
		super().__init__(name)

		this.arg.kw.required.append("sql_host")
		this.arg.kw.required.append("sql_db")
		this.arg.kw.required.append("sql_user")
		this.arg.kw.required.append("sql_pass")

		this.arg.kw.required.append("redis_host")
		
		this.arg.kw.optional["sql_engine"] = "mysql"
		this.arg.kw.optional["sql_port"] = 3306
		this.arg.kw.optional["sql_ssl"] = False

		this.arg.kw.optional["redis_port"] = 6379
		this.arg.kw.optional["redis_db"] = 0
		this.arg.kw.optional["redis_semaphore_timeout"] = 1800 # Timeout for semaphore locks (seconds). Should only be used if a server crashed, etc.

		this.sqlEngine = None
		this.sql = None
		this.redis = None

	def Function(this):
		this.sqlEngine = create_async_engine(f"{this.sql_engine}://{this.sql_user}:{this.sql_pass}@{this.sql_host}:{this.sql_port}/{this.sql_db}")
		this.sql = sqlalchemy.orm.sessionmaker(
			this.sqlEngine,
			expire_on_commit=False, 
    		class_=AsyncSession
		)
		this.redis = redis.asyncio.Redis(host=this.redis_host, port=this.redis_port, db=this.redis_db)

	
	async def Close(this):
		if (this.sqlEngine):
			logging.debug("Closing SQL connection")
			await this.sqlEngine.dispose()
		if (this.redis):
			logging.debug("Closing Redis connection")
			await this.redis.close()

	
	# Get the state of a process on an inode.
	# RETURNS the state for the given process on the given inode or None if there was an error.
	async def GetState(this, inode, process):
		try:
			state = await this.GetRedisInodeValue(inode, process)
			if (state is None):
				return None
			return ProcessState(int(state))
		except Exception as e:
			logging.error(f"Error getting state for {inode}:{process}: {e}")
			return None

	# Set the state of a process on an inode.
	# For extra safety, you can pass in what you think the current state is. If it's not what you expect, the state will not be set.
	async def SetState(this, inode, process, state, expectedState=None):
		stateValue = str(state.value)  # Store the enum value as a string
		expectedStateValue = str(expectedState.value) if expectedState is not None else None
		ret = await this.SetRedisInodeValue(inode, process, stateValue, expectedStateValue)
		return ret


	# Get a value for a key on an inode in Redis.
	# If you need to coerce the value to a specific type, pass in the type as coerceType.
	# RETURNS the value for the given key on the given inode or None if there was an error.
	async def GetRedisInodeValue(this, inode, key, coerceType=None):
		try:
			ret = await this.redis.get(f"{inode}:{key}")
			if (ret is None):
				return None

			ret = ret.decode('utf-8')

			if (ret == "__NONE__"):
				return None

			if (coerceType is not None):
				if (coerceType == bool):
					ret = ret.lower() == "true"
				elif (coerceType in [int, float]):
					if (not len(ret)):
						return None
					if (ret.isdigit() or (ret[0] == '-' and ret[1:].isdigit())):
						ret = int(ret)
					else:
						return None
				else:
					ret = coerceType(ret)

			return ret
		except Exception as e:
			logging.error(f"Error getting value for {inode}:{key}: {e}")
			return None

	# Set a value for a key on an inode in Redis.
	# For extra safety, you can pass in what you think the current value is. If it's not what you expect, the value will not be set.
	# For example, if a long time has passed between when you last checked the value and when you set it, you can use the return value of this method let you know if you need to recheck your data.
	# RETURNS True if the value was set, False otherwise.
	async def SetRedisInodeValue(this, inode, key, value, expectedValue=None):
		ret = False

		if (value is None):
			value = "__NONE__"
		value = str(value).encode('utf-8')

		if (expectedValue is not None):
			expectedValue = str(expectedValue)
			lua = """\
if redis.call('GET', KEYS[1]) == ARGV[1] then
	redis.call('SET', KEYS[1], ARGV[2])
	redis.call('EXPIRE', KEYS[1], tonumber(ARGV[3]))
	return 1
else
	return 0
end
"""
			try:
				result = await this.redis.eval(lua, 1, f"{inode}:{key}", expectedValue, value, this.redis_semaphore_timeout)
				ret = result == 1 and await this.GetRedisInodeValue(inode, key) == value
			except Exception as e:
				logging.error(f"Error setting value for {inode}:{key} to {value}: {e}")
				ret = False

		else:
			try:
				await this.redis.set(f"{inode}:{key}", value, ex=this.redis_semaphore_timeout)
				ret = await this.GetRedisInodeValue(inode, key) == value
			except Exception as e:
				logging.error(f"Error setting value for {inode}:{key} to {value}: {e}")
				ret = False

		return ret

class Daemon(eons.StandardFunctor):
	def __init__(this, name="Daemon"):
		super().__init__(name)
		
		this.arg.kw.optional["nice"] = 19
		this.arg.kw.optional["sleep"] = 60

		this.lock = asyncio.Lock()
		this.stop = False


	@classmethod
	def Run(cls, executorArgs, name=None):
		if (name is None):
			daemon = cls()
		else:
			daemon = cls(name)

		# Initialize the Executor.
		try:
			executor = RiverFS(f"RiverFS Background Process: {daemon.name}")
			for key, value in executorArgs.items():
				executor.main_process.arg[key] = value
			executor()
		except Exception as e:
			logging.error(f"Error initializing {this.name}: {e}")
			raise e

		if ('parent_pid' in executorArgs):
			daemon.parent_pid = executorArgs['parent_pid']

		daemon.executor = executor
		daemon()
		executor.Stop()
		sys.exit(0)


	# Function is the main entry point for eons.Functor objects.
	# We use this as the entry point to fork over to our Worker() method.
	def Function(this):
		try:
			os.nice(this.nice)
		except Exception as e:
			logging.error(f"{this.name} (PID: {os.getpid()}): Error setting low priority: {e}")

		logging.info(f"Starting Daemon: {this.name} (PID: {os.getpid()}, Priority: {this.nice}, Interval: {this.sleep} seconds)")
		this.executor.Async(this.WorkerLoop(), timeout=None)


	async def WorkerLoop(this):
		# Run indefinitely.
		while True:
			async with this.lock:
				if (this.stop):
					logging.info(f"{this.name} (PID: {os.getpid()}): Stopping Worker")
					break

			try:
				logging.debug(f"{this.name} (PID: {os.getpid()}): Running Worker")
				await this.Worker()
			except Exception as e:
				logging.error(f"Error in Daemon: {e}")
				eons.util.LogStack()

			await asyncio.sleep(this.sleep)

	# TODO: How do we call this?
	async def Stop(this):
		logging.info(f"Signalling {this.name} (PID: {os.getpid()}) to stop.")
		async with this.lock:
			this.stop = True


	async def Worker(this):
		#
		# YOUR CODE GOES HERE
		#
		pass


class CachePruneDaemon(Daemon):
	def __init__(this, name="Cache Prune Daemon"):
		super().__init__(name)
		this.arg.kw.optional["sleep"] = 3600


	async def Worker(this):
		current_time = time.time()
		ttl = this.executor.cache_ttl  # cache_ttl (in seconds) should be defined on the executor.

		try:
			session = this.executor.GetDatabaseSession()
			# Select inodes that:
			# - Have a non-null data field (i.e. cached file exists),
			# - Haven't been accessed recently (last_accessed < current_time - ttl),
			# - And are not pending any operations.
			query = await session.execute(select(InodeModel).where(
				InodeModel.data.isnot(None),
				InodeModel.cap_rw.startswith("URI:"),
				InodeModel.last_accessed < (current_time - ttl),
				InodeModel.pending_sync == False,
				InodeModel.pending_creation == False,
				InodeModel.pending_deletion == False
			))
			inodes = query.scalars().all()
		except Exception as e:
			logging.error(f"{this.name}: Error querying database: {e}")
			try:
				await session.close()
			except:
				pass
			return

		for inode in inodes:
			file_path = inode.data
			if file_path and os.path.exists(file_path):
				try:
					os.remove(file_path)
					logging.info(f"{this.name}: Removed cached file '{file_path}' for inode {inode.id}")
				except Exception as e:
					logging.error(f"{this.name}: Error removing file '{file_path}': {e}")
					continue
			else:
				logging.debug(f"{this.name}: File '{file_path}' does not exist for inode {inode.id}")

				logging.debug(f"{this.name}: Cleared cache file for inode {inode}")

			logging.debug(f"{this.name}: Clearing cache db entry for inode {inode.id}")
			inode.data = None

			logging.debug(f"{this.name}: Expiring inode {inode.id}")
			await this.executor.delta.SetRedisInodeValue(inode.id, "last_written", time.time())

			try:
				await session.commit()
			except Exception as e:
				logging.error(f"{this.name}: Error committing update for inode {inode.id}: {e}")
				await session.rollback()

		await session.close()


# Ignore local imports; they'll be added by the build process.

class GarbageDaemon(Daemon):
	def __init__(this, name="Garbage Daemon"):
		super().__init__(name)


	async def Worker(this):
		current_time = time.time()
		ttl = this.executor.cache_ttl  # cache_ttl (in seconds) should be defined on the executor.

		try:
			session = this.executor.GetDatabaseSession()
			query = await session.execute(select(InodeModel).where(
				InodeModel.pending_deletion == True
			))
			inodeModels = query.scalars().all()
			inodes = []
			for model in inodeModels:
				inode = await Inode.From(this.executor, model.upath, createIfNotExists=False, allowSync=False)
				if (inode is not None):
					inodes.append(inode)
			await session.close()
		except Exception as e:
			logging.error(f"{this.name}: Error querying database: {e}")
			return

		for inode in inodes:
			if (await inode.IsStateLocked('sync')):
				# Another process is handling this. We'll get back to it later if it still needs deletion.
				continue

			logging.debug(f"{this.name}: Initiating deletion of {inode.StringId()}")
			await inode.SetState('sync', ProcessState.RUNNING)
			await inode.SetState('delete', ProcessState.RUNNING)
			await inode.SetEphemeral('sync_host', socket.gethostname(), expectedValue="")
			await inode.SetEphemeral('sync_pid', os.getpid(), expectedValue="")

			# Inodes should know how to delete themselves, so we'll just initiate their deletion here.
			# NOTE: inode.InitiateSync("UP") won't work here, cause we can't spawn a child daemon.
			await TahoeSyncWorker.PushUpstreamToSource(this.executor, inode)

			# The inode should be invalid, but we'll update the states just to be nice.
			await inode.SetState('delete', ProcessState.COMPLETE)
			await inode.SetState('sync', ProcessState.COMPLETE)


class ReaperDaemon(Daemon):
	def __init__(this, name="Reaper Daemon"):
		super().__init__(name)

		this.arg.kw.optional["max_runtime"] = 14400  # Max total lifetime of a worker.
		this.arg.kw.optional["sleep_timeout"] = 60  # Max time to allow a worker to sleep before killing it.

		this.stats = eons.util.DotDict()
		this.stats.proc = eons.util.DotDict()
		this.stats.proc.count = 0
		this.stats.proc.by_reason = {
			"long_running": 0,
			"idle": 0,
			"error": 0
		}
		this.stats.proc.runtime = eons.util.DotDict()
		this.stats.proc.runtime.total = 0
		this.stats.proc.runtime.average = 0
		this.stats.proc.runtime.rolling = eons.util.DotDict()
		this.stats.proc.runtime.rolling.last_hour = []  # list of (timestamp, runtime)

		this.lastActive = {}

	async def Worker(this):
		now = time.time()
		workers = this.executor.shared_workers
		if (not workers):
			logging.debug(f"{this.name}: No tracked workers found.")
			return

		reaped = 0
		alive = 0

		for entry in list(workers):
			pid = entry.get("pid")
			inode_id = entry.get("inode")
			started = entry.get("started", 0)
			lastActive = this.lastActive.get(pid, started)
			reason = None

			try:
				proc = psutil.Process(pid)
				runtime = now - started

				try:
					cpu = proc.cpu_percent(interval=0.1)
					logging.debug(f"{this.name}: PID {pid} CPU usage: {cpu}")
				except Exception as e:
					logging.warning(f"{this.name}: Failed to get CPU usage for PID {pid}: {e}")
					cpu = 0.0

				if (cpu > 0.0):
					this.lastActive[pid] = now
					lastActive = now

				if (runtime > this.max_runtime):
					proc.terminate()
					reason = "long_running"
					this.lastActive.pop(pid, None)
					logging.warning(f"{this.name}: Terminated long-running worker PID {pid} (inode {inode_id}) after {runtime:.2f}s")

				elif (proc.status() == psutil.STATUS_SLEEPING and (now - lastActive) > this.sleep_timeout):
					proc.terminate()
					reason = "idle"
					this.lastActive.pop(pid, None)
					logging.debug(f"{this.name}: Terminated idle worker PID {pid} (inode {inode_id}) idle for {(now - lastActive):.2f}s")

				# Check if process is gone after termination attempt
				if (reason is not None):
					this.stats.proc.count += 1
					this.stats.proc.by_reason[reason] += 1
					this.stats.proc.runtime.total += runtime
					this.stats.proc.runtime.rolling.last_hour.append((now, runtime))

					reaped += 1
					logging.info(f"{this.name}: Reaped PID {pid} (inode {inode_id}) reason: {reason}, runtime: {runtime:.2f}s")
				else:
					alive += 1

			except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
				logging.debug(f"{this.name}: Skipped PID {pid}: {e}")
			except Exception as e:
				logging.warning(f"{this.name}: Error handling PID {pid}: {e}")
				this.stats.proc.by_reason["error"] += 1

		# Prune stats older than 1 hour
		cutoff = now - 3600
		this.stats.proc.runtime.rolling.last_hour = [
			(ts, rt) for ts, rt in this.stats.proc.runtime.rolling.last_hour if ts >= cutoff
		]

		if (this.stats.proc.runtime.rolling.last_hour):
			total_runtime = sum(rt for _, rt in this.stats.proc.runtime.rolling.last_hour)
			this.stats.proc.runtime.average = total_runtime / len(this.stats.proc.runtime.rolling.last_hour)
		else:
			this.stats.proc.runtime.average = 0

		logging.debug(
			f"{this.name}: {alive} alive | {reaped} reaped this pass | "
			f"{this.stats.proc.count} total | avg runtime {this.stats.proc.runtime.average:.2f}s"
		)

		logging.debug(
			f"{this.name} totals — "
			f"long_running: {this.stats.proc.by_reason['long_running']}, "
			f"idle: {this.stats.proc.by_reason['idle']}, "
			f"errors: {this.stats.proc.by_reason['error']}"
		)


class TahoeConnection(eons.Functor):
	def __init__(this, name="Tahoe Connection"):
		super().__init__(name=name)
		this.arg.kw.required.append('base_url')
		this.arg.kw.required.append('rootcap')
		this.arg.kw.optional['timeout'] = 10
		this.arg.kw.optional['max_connections'] = 10
		this.arg.kw.optional['auth_token'] = None

		this.arg.mapping.append('base_url')
		this.arg.mapping.append('rootcap')
		this.arg.mapping.append('timeout')

		this.api_version = "/v1"
		this.lock = asyncio.Lock()
		this.session = None  # aiohttp session

	def ValidateArgs(this):
		super().ValidateArgs()
		assert isinstance(this.base_url, str), this.base_url
		assert isinstance(this.rootcap, str), this.rootcap
		assert isinstance(this.timeout, (int, float)), this.timeout

		# Normalize the base URL and encode the root capability.
		this.base_url = f"{this.base_url.rstrip('/')}/uri"
		this.rootcap = this.rootcap.encode('utf-8')

		# Create separate semaphores for PUT and GET requests.
		put_conns = max(1, this.max_connections // 2)
		get_conns = max(1, this.max_connections - put_conns)
		this.get_semaphore = asyncio.Semaphore(get_conns)
		this.put_semaphore = asyncio.Semaphore(put_conns)

	async def Open(this):
		if this.session:
			await this.Close()
		this.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=this.timeout))

	async def Close(this):
		if this.session:
			try:
				logging.debug("Closing tahoe connection")
				await this.session.close()
			except Exception as e:
				logging.error(f"Error closing tahoe connection: {e}")
			finally:
				this.session = None

	async def SendRequest(this, method, url, headers, data, is_put):
		if (this.auth_token):
			headers['Authorization'] = f'Bearer {this.auth_token}'

		semaphore = this.put_semaphore if is_put else this.get_semaphore
		async with semaphore:
			response = await this.session.request(method, url, headers=headers, data=data)
			if (response.status >= 400):
				error_text = await response.text()
				logging.error(f"HTTP {response.status} error for {url}: {error_text}")
				response.close()  # Make sure to close if error occurs.
				response.raise_for_status()
			logging.debug(f"Request for {url} returned {response.status}")
			return response  # Caller is now responsible for closing the response.


	def Url(this, path, params={}, iscap=False):
		# Quote the path to safely insert it into a URL.
		path = quote(path).lstrip('/')
		if iscap:
			full_url = f"{this.base_url}/{path}"
		else:
			# Use the decoded rootcap for non-iscap URLs.
			full_url = f"{this.base_url}/{this.rootcap.decode('ascii')}/{path}"

		if params:
			query = '&'.join([f"{quote(str(k))}={quote(str(v))}" for k, v in params.items()])
			full_url += '?' + query

		return full_url

	def GetRequest(this, method, path, offset=None, length=None, data=None, params={}, iscap=False):
		headers = {'Accept': 'application/json'}
		if offset is not None or length is not None:
			start = str(offset) if offset is not None else "0"
			end = str(offset + length - 1) if length is not None else ""
			headers['Range'] = f'bytes={start}-{end}'
		url = this.Url(path, params=params, iscap=iscap)
		return {"method": method, "url": url, "headers": headers, "data": data}

	async def Get(this, path, params={}, offset=None, length=None, iscap=False):
		req = this.GetRequest("GET", path, offset=offset, length=length, params=params, iscap=iscap)
		response = await this.SendRequest(req["method"], req["url"], req["headers"], req["data"], is_put=False)
		return response

	async def Post(this, path, data=None, params={}, iscap=False):
		req = this.GetRequest("POST", path, data=data, params=params, iscap=iscap)
		response = await this.SendRequest(req["method"], req["url"], req["headers"], req["data"], is_put=False)
		return response

	async def Put(this, path, data=None, params={}, iscap=False, file_format="MDMF"):
		# Include the file format in the query parameters.
		params["format"] = file_format
		req = this.GetRequest("PUT", path, data=data, params=params, iscap=iscap)
		response = await this.SendRequest(req["method"], req["url"], req["headers"], req["data"], is_put=True)
		return response

	async def Delete(this, path, params={}, iscap=False):
		req = this.GetRequest("DELETE", path, params=params, iscap=iscap)
		response = await this.SendRequest(req["method"], req["url"], req["headers"], req["data"], is_put=False)
		return response

	async def Head(this, path, params={}, iscap=False):
		req = this.GetRequest("HEAD", path, params=params, iscap=iscap)
		response = await this.SendRequest(req["method"], req["url"], req["headers"], req["data"], is_put=False)
		response.close()  # Close the response to avoid reading the body.
		return response

	# Unlink all files and directories under the rootcap.
	# USE WITH EXTREME CAUTION!!!
	async def NukeRoot(this):
		logging.critical("Nuking Tahoe root directory...")

		try:
			response = await this.Get("", params={"t": "json"})
			text = await response.text()
			content_type = response.headers.get("Content-Type", "unknown")
			logging.debug(f"Content-Type: {content_type}")
			response.close()

			try:
				dir_data = json.loads(text)
			except json.JSONDecodeError as e:
				logging.error(f"Failed to parse JSON: {e}")
				logging.debug(f"Response text: {text}")
				return

		except Exception as e:
			logging.error(f"Failed to list Tahoe rootcap contents: {e}")
			return

		# === New API: S-expression style JSON ===
		# Expecting: ['dirnode', {'children': {'name': ['filenode', {...}], ...}}]
		if isinstance(dir_data, list) and len(dir_data) == 2 and isinstance(dir_data[1], dict):
			dir_type, dir_meta = dir_data
			if dir_type != "dirnode":
				logging.error(f"Rootcap is not a directory: type={dir_type}")
				return
			children_dict = dir_meta.get("children", {})
		else:
			logging.error("Unexpected directory JSON format. Cannot proceed.")
			logging.debug(f"dir_data: {dir_data}")
			return

		if not children_dict:
			logging.info("Tahoe root directory is already empty.")
			return

		# Unlink each child by its key name
		for child_name in children_dict:
			try:
				logging.info(f"Deleting '{child_name}'...")
				unlink_data = aiohttp.FormData()
				unlink_data.add_field("t", "unlink")
				unlink_data.add_field("name", child_name)

				res = await this.Post("", data=unlink_data)
				res.close()
				logging.debug(f"Successfully deleted '{child_name}'")
			except Exception as e:
				logging.error(f"Failed to delete '{child_name}': {e}")

		logging.critical("Tahoe root directory nuked.")


# Filesystem operations typically occur in stages.
class Stage(Enum):
	INVALID = 0
	TAHOE = 1
	DATABASE = 2
	CACHE = 3

	def __str__(self):
		return self.name

class CacheStrategy(Enum):
	# Error state - something went wrong.
	ERROR = 0

	# Never cache this file.
	# NOTE: if TahoeFS exits before the file is synced, the file will be lost.
	NEVER = 1

	# Cache this file only when explicitly requested (i.e. when the file data have changed)
	ONDEMAND = 2

	# Do not sync this file to the backend - it will only be stored locally.
	ONLY = 3


	def __str__(self):
		return self.name

# The storage strategy governs how files and folders are managed in Tahoe.
# The goal in making this a feature choice is that we can improve strategies over time and allow users to upgrade their strategy when they are ready.
class StorageStrategy(enum.Enum):
	NONE = 0

	# This strategy mirrors the requested filesystem hierarchy in Tahoe.
	# In order for a file or folder to be created, its parent must already exist in Tahoe.
	# The main drawback to this strategy is that we must:
	# 1. wait for the parent to be created before creating the child
	# 2. handle move operations in Tahoe in addition to locally
	# 3. propagate directory deletes for all sub-folders in order to ensure proper garbage collection in Tahoe
	MIRROR = 1

	# This strategy puts all files under the Tahoe rootcap.
	# The advantage this offers compared to the above strategy is that create, move, and delete operations can rely on the database, without having to wait for Tahoe.
	# The main drawback is that we potentially run into performance issues when storing upwards of millions of files in Tahoe.
	FLAT = 2

	# TODO: Explore a round-robin load balancing strategy across a pool of folders in Tahoe.

	def __str__(self):
		return self.name

# Sleep for exponentially increasing time. `n` is the number of times
# sleep has been called.
async def ExponentialSleep(n, start=0.1, max_sleep=60):
	sleep_time = min(start * (2**n), max_sleep)
	await asyncio.sleep(sleep_time)


def parse_size(size_str):
	multipliers = {
		't': 1000**4,
		'g': 1000**3,
		'm': 1000**2,
		'k': 1000**1,
		'tb': 1000**4,
		'gb': 1000**3,
		'mb': 1000**2,
		'kb': 1000**1,
		'tib': 1024**4,
		'gib': 1024**3,
		'mib': 1024**2,
		'kib': 1024**1,
	}
	size_re = re.compile(r'^\s*(\d+)\s*(%s)?\s*$' % ("|".join(list(multipliers.keys())),), 
						 re.I)

	m = size_re.match(size_str)
	if not m:
		raise ValueError("not a valid size specifier")

	size = int(m.group(1))
	multiplier = m.group(2)
	if multiplier is not None:
		try:
			size *= multipliers[multiplier.lower()]
		except KeyError:
			raise ValueError("invalid size multiplier")

	return size


def parse_lifetime(lifetime_str):
	if (type(lifetime_str) == int):
		return lifetime_str

	if lifetime_str.lower() in ('inf', 'infinity', 'infinite'):
		return 100*365*24*60*60

	try:
		return int(lifetime_str)
	except ValueError:
		raise ValueError("invalid lifetime specifier")

class TruckeeFSException(Exception, metaclass=eons.ActualType): pass
class TruckeeFSInodeException(TruckeeFSException, metaclass=eons.ActualType): pass
# from truckeefs.lib.db.InodeModel import InodeModel #implicit per build system.
# TahoeSyncWorker is implicit per build system.

class Inode (eons.Functor):
	defaultPermissions = 0o755

	def __init__(
		this,
		upath=None,
		name=None,
		meta={}
	):
		super().__init__(name)

		this.id = None
		this.meta = {
			'atime': time.time(),
			'mtime': time.time(),
			'ctime': time.time(),
			'atime_ns': 0,
			'mtime_ns': 0,
			'uid': os.getuid(),
			'gid': os.getgid(),
			'mode': this.defaultPermissions,
			'xattr': {},
		}
		this.meta.update(meta)

		this.upath = upath
		this.paths = []
		this.parents = [] # parent ids

		this.cap = eons.util.DotDict()
		this.cap.ro = None
		this.cap.rw = None
		
		this.cache = eons.util.DotDict()
		this.cache.strategy = CacheStrategy.ONDEMAND

		if (upath and type(upath) is str):
			# We need to keep upath out of this.paths so that the this.parents can be populated by this.AddPath()
			# if (upath not in this.paths):
			# 	this.paths.append(upath)
			if (name is None):
				this.name = upath.split('/')[-1]

		this.arg.kw.required.append('db')

		this.stateRetries = 15 # Number of times to retry a state check. Uses ExponentialSleep between tries.

		# Temporary Sync operational members.
		# Do not modify these directly.
		this.frozen = None # Data to be synced to Tahoe as JSON. Do not modify directly.
		this.sync = eons.util.DotDict() # Sync-related data for the object.
		this.sync.allowed = True # "daemonic processes are not allowed to have children"
		this.sync.when = eons.util.DotDict() # When to sync the object.
		this.sync.when.mutated = True # Whether to sync the object when it is mutated.
		this.sync.when.deleted = True # Whether to sync the object when it is deleted.
		this.time = eons.util.DotDict() # Time-related data for the object.
		this.time.accessed = time.time() # Last time the object was read; NOTE: this is distinct from the 'atime' metadata.
		this.time.retrieved = 0 # Last time the object was retrieved from Tahoe.
		this.time.synced = 0 # Last time the object was synced to Tahoe or the Database.

		# Additional attributes for internal bookkeeping.
		this.pending = eons.util.DotDict()
		this.pending.sync = False  # Flag for pending sync operations.
		this.pending.create = False  # Flag for pending create operations.
		this.pending.delete = False  # Flag for pending delete operations.

		this.kind = "Inode"


	def StringId(this):
		return f"{this.__class__.__name__} for '{this.upath}' (id: {this.id})"


	# Get the state of a process on an inode.
	# Use this method for semaphore operations.
	# Processes include 'read', 'write', and 'sync'.
	async def GetState(this, process):
		ret = await this.executor.delta.GetState(this.id, process)
		logging.debug(f"Got State for {this.StringId()}: {process} -> {ret}.")
		return ret

	# Get the state of a process on an inode.
	# Use this method for semaphore operations.
	# Processes include 'read', 'write', and 'sync'.
	# For extra safety, you can pass in what you think the current state is. If it's not what you expect, the state will not be set.
	# RETURNS True if the state has been set. False otherwise.
	async def SetState(this, process, state, expectedState=None):
		return await this.executor.delta.SetState(this.id, process, state)

	# Wait for a process to reach a certain state.
	async def WaitForState(this, process, state):
		for i in range(this.stateRetries):
			if (await this.GetState(process) == state):
				return True

			await ExponentialSleep(i)

		return False
	
	# Wait for a process to reach a state besides the one provided.
	# RETURNS the new state if it changes. False otherwise.
	async def WaitForStateBesides(this, process, state):
		for i in range(this.stateRetries):
			newState = await this.GetState(process)
			if (newState != state):
				return newState

			await ExponentialSleep(i)

		return False

	# Wait for a process to change state.
	# RETURNS the new state if it changes. False otherwise.
	async def WaitForStateChange(this, process):
		return await this.WaitForStateBesides(process, await this.GetState(process))

	# Check if the current state implies an ongoing operation, possibly in another process.
	# RETURNS True if the state is available to be changed to PENDING or RUNNING. False otherwise.
	async def IsStateLocked(this, process):
		state = await this.GetState(process)
		if (state is None):
			return False

		if (state in [ProcessState.PENDING, ProcessState.RUNNING]):
			return True

		return False

	# Check if the process states for this inode have been initialized.
	# RETURNS True if the states have been initialized. False otherwise.
	async def AreProcessStatesInitialized(this):
		
		# Whether or not the user has *this open for reading.
		# If this is locked, we can sync the file at will, knowing it won't be changed.
		readState = await this.GetState('read')

		# Whether or not the user has *this open for writing.
		# If this is locked, we can't sync the file until the user is done writing.
		# The exception is if the user deletes the file, then we can sync that.
		writeState = await this.GetState('write')

		# Where *this is in the process of being deleted.
		# IDLE means not deleted.
		deleteState = await this.GetState('delete')

		# Where *this is in the process of being synced.
		# Indicates the state of the background sync task.
		# Can be ignored, but if we're feeling generous, we can wait for a sync to finish before mutating the object.
		syncState = await this.GetState('sync')

		# If any one state is None, there might just be a network error (though we hope not!)
		# If all states are None, the object should be initialized.
		if (
			readState is None 
			and writeState is None
			and deleteState is None
			and syncState is None
		):
			return False
		
		return True

	# Initialize the process states for this inode.
	async def InitializeProcessStates(this):
		logging.debug(f"Initializing Process States for {this.StringId()}.")
		await this.SetState('read', ProcessState.IDLE)
		await this.SetState('write', ProcessState.IDLE)
		await this.SetState('delete', ProcessState.IDLE)
		await this.SetState('sync', ProcessState.IDLE)


	# Get a value for a key on an Inode in Redis.
	# If you need to coerce the value to a specific type, pass in the type as coerceType.
	# RETURNS the value, as a string, for the given key on the given Inode or None if there was an error.
	async def GetEphemeral(this, key, coerceType=None):
		ret = await this.executor.delta.GetRedisInodeValue(this.id, key, coerceType)
		logging.debug(f"Got Ephemeral {key} for {this.StringId()}: {ret}")
		return ret

	# Set a value for a key on an Inode in Redis.
	# RETURNS True if the value was set, False otherwise.
	# Use the expectedValue parameter for extra safety. If the value is not what you expect, the value will not be set.
	async def SetEphemeral(this, key, value, expectedValue=None):
		logging.debug(f"Setting Ephemeral {key} to {value} of {this.StringId()}.")
		return await this.executor.delta.SetRedisInodeValue(this.id, key, value, expectedValue)

	# Set any temporary values to their default values.
	# NOTE: These are less structerd than the process states, so there's no Are...Initialized methods.
	# Because of that, this method should be called wherever InitializeProcessStates is called.
	async def InitializeEphemerals(this):
		logging.debug(f"Initializing Ephemerals of {this.StringId()}.")
		await this.SetEphemeral('sync_pid', "")
		await this.SetEphemeral('sync_host', "")
		await this.SetEphemeral('sync_again', False)
		await this.SetEphemeral('last_written', "")


	@classmethod
	async def GetFromCache(
		cls,
		executor,
		upath,
		createIfNotExists=False,
		meta=None,
		allowSync=True,
	):
		ret = executor.GetCachedInodeByUpath(upath)
		if (ret is not None):
			ret.sync.allowed = allowSync

			# A upath mismatch here should indicate the file was moved.
			if (not await ret.IsFresh() or ret.upath != upath):
				await executor.PurgeCachedInode(ret)
				logging.debug(f"Cache of {ret.StringId()} is stale.")
				return None

			# We can't operate on a directory that hasn't been created, since it won't have a Tahoe capability.
			# WARNING: This will deadlock file creation, since the sync worker waits on the file to be closed.
			# NOTE: This only applies to the MIRROR Strategy.
			if (
				cls == Directory # Not File, per above
				and executor.strategy.storage == StorageStrategy.MIRROR
				and ret.pending.create 
				and await ret.IsStateLocked('sync')):
				logging.debug(f"Waiting for {ret.StringId()} to be created...")
				await ret.WaitForState('sync', ProcessState.COMPLETE)
				logging.debug(f"{ret.StringId()} has been created. Purging cache.")
				await executor.PurgeCachedInode(ret)
				return None

			logging.debug(f"{ret.StringId()} found in cache.")

		return ret


	@classmethod
	async def GetFromDatabase(
		cls,
		executor,
		upath,
		createIfNotExists=False,
		meta=None,
		allowSync=True,
	):
		obj = None
		session = executor.GetDatabaseSession()
		try:
			query = await session.execute(select(InodeModel).where(InodeModel.upath == upath).options(
				orm.joinedload(InodeModel.parents).load_only(InodeModel.id),
				orm.joinedload(InodeModel.children).load_only(InodeModel.id)
			))
			obj = query.scalar()
		except NoResultFound:
			logging.debug(f"Inode for '{upath}' not in database.")
			await session.close()
			return None

		if (obj is None):
			logging.debug(f"Inode for '{upath}' not in database.")
			await session.close()
			return None

		# TODO: Let's make this more extensible.
		kind = cls
		if (obj.kind == "Directory"):
			kind = Directory
		elif (obj.kind == "File"):
			kind = File

		ret = kind(upath)
		ret.id = obj.id
		ret.sync.allowed = allowSync
		ret.executor = executor
		await ret.LoadFromData(obj)
		await ret.OnLoad()
		await session.close()
		logging.debug(f"Loaded {ret.StringId()} from database.")
		return ret


	@classmethod
	async def Create(
		cls,
		executor,
		upath,
		meta=None,
		allowSync=True,
	):
		if (not allowSync):
			logging.error(f"Cannot create {cls.__name__} for '{upath}' without allowing sync.")
			raise Exception(f"Cannot create {cls.__name__} for '{upath}' without allowing sync.")

		logging.debug(f"Creating new {cls.__name__} for '{upath}'.")

		name = upath.split('/')[-1]
		ret = cls(upath, name)
		ret.executor = executor
		ret.meta.update(meta)
		ret.pending.create = True
		ret.kind = cls.__name__
		session = executor.GetDatabaseSession()
		inode = InodeModel()
		inode.upath=upath
		inode.name=ret.name
		inode.kind=ret.kind
		inode.parents=[]
		inode.meta=ret.meta
		inode.cache_strategy=ret.cache.strategy.name
		inode.cap_ro=ret.cap.ro
		inode.cap_rw=ret.cap.rw
		inode.pending_sync=ret.pending.sync
		inode.pending_creation=ret.pending.create
		inode.pending_deletion=ret.pending.delete

		session.add(inode)
		await session.commit()
		ret.id = inode.id

		# Close the session so that we're not holding on to any model locks.
		await session.close()

		ret.pending.create = True
		await ret.AddPath(upath, save=False) # Populate the parents list (after the inode exists in the db)
		await executor.CacheInode(ret) # Will initialize Ephemerals
		await ret.OnLoad()
		logging.debug(f"Created new {ret.StringId()}.")
		return ret


	# Factory method to create a new Inode from a given upath
	@classmethod
	async def From(
		cls,
		executor,
		upath,
		createIfNotExists=False,
		meta=None, # Additional metadata to add to the Inode only upon create.
		allowSync=True,
	):
		if (meta is None):
			meta = {}

		if (upath.startswith('/')):
			upath = upath[1:]

		logging.debug(f"Getting Inode for '{upath}'.")

		ret = await cls.GetFromCache(executor, upath, createIfNotExists, meta, allowSync)
		if (ret is None):
			ret = await cls.GetFromDatabase(executor, upath, createIfNotExists, meta, allowSync)
		if (ret is None and createIfNotExists):
			ret = await cls.Create(executor, upath, meta, allowSync)
		if (ret is None):
			raise TruckeeFSInodeException(f"Inode for '{upath}' does not exist.")

		if (ret.kind != cls.__name__ and cls.__name__ != "Inode"): # Base class is okay.
			raise TruckeeFSInodeException(f"Cannot create {cls.__name__} for '{upath}'; existing Inode is a {ret.kind}.")

		# This could happen if the Inode was deleted by another process
		# or we're simply recreating something we deleted.
		if (not createIfNotExists and await ret.GetState('delete') == ProcessState.COMPLETE):
			raise FileNotFoundError(errno.ENOENT, f"{ret.StringId()} has been deleted.")

		return ret

	
	@classmethod
	async def FromId(
		cls,
		executor,
		id,
		allowSync=True,
	):
		logging.debug(f"Getting Inode for id {id}.")
		upath = None

		session = executor.GetDatabaseSession()
		query = await session.execute(select(InodeModel).where(InodeModel.id == id))
		obj = query.scalar()
		upath = obj.upath
		await session.close()

		return await cls.From(executor, upath, createIfNotExists=False, allowSync=allowSync)


	# Validate the arguments provided to the object.
	# eons.Functor method. See that class for more information.
	def ValidateArgs(this):
		super().ValidateArgs()

		if (not this.id):
			if (not len(this.upath)):
				raise eons.MissingArgumentError(f"No upath provided for {this.__class__.__name__} {this.name}")


	# Add a new path to *this.
	# This will not change the canonical upath.
	# Implies the possible addition of a new parent.
	async def AddPath(this, path, save=True):
		if (not len(path)):
			return

		if (path not in this.paths):
			this.paths.append(path)

			if (path != '' and path != '/'):
				# NOTE: Directory cannot be imported, but should be available.
				parent = await Directory.From(this.executor, os.path.dirname(path))
				if (parent is None):
					logging.error(f"Parent of {this.StringId()} not found.")
					raise FileNotFoundError(errno.ENOENT, f"Parent of {this.StringId()} not found.")

				if (parent.id not in this.parents):
					this.parents.append(parent.id)
					await parent.AddChild(this)

				# Don't save if the parent already exists.
				if (save):
					await this.Save(mutated=False)

	# Get the Directory Inode that contains *this.
	async def GetParent(this):
		# This check might cause issues when moving or copying files.
		# if (len(this.parents) == 0):
		# 	return None

		parent_path = os.path.dirname(this.upath)
		ret = await Directory.From(this.executor, parent_path, allowSync=this.sync.allowed)
		logging.debug(f"Parent of {this.StringId()} is {ret.StringId()}.")
		return ret

	async def WasJustWrittenTo(this):
		lastWritten = await this.GetEphemeral('last_written', coerceType=int)

		if (not await this.IsFresh()):
			logging.debug(f"{this.StringId()} was written to by another process.")
			return False

		now = int(time.time())
		await this.SetEphemeral('last_written', now)
		this.time.synced = now
		logging.debug(f"{this.StringId()} was just written to at {now}.")
		return True

	# Helper function to update metadata on access.
	# RETURNS the time now.
	async def Accessed(this, save=True):
		if (this.pending.delete):
			raise FileNotFoundError(errno.ENOENT, f"{this.StringId()} has been deleted.")

		now = time.time()
		this.time.accessed = now
		this.meta['atime'] = now
		if (save):
			await this.Save(mutated=False)
		return now

	# Check if the object is still fresh in the cache
	# Will return False if the object has been written to by another process.
	async def IsFresh(this):
		lastWritten = await this.GetEphemeral('last_written', coerceType=int)
		if (lastWritten is None):
			lastWritten = 0
		if (lastWritten > this.time.synced):
			return False
		return True


	# RETURNS a dictionary of the data that should be saved to the database.
	# You should override this method in your child class to save additional data.
	async def GetDataToSave(this, session):
		query = await session.execute(select(InodeModel).where(InodeModel.id.in_(this.parents)))
		parentList = query.scalars().all()

		return {
			"upath": this.upath,
			"name": this.name,
			"kind": this.__class__.__name__,
			"parents": parentList,
			"meta": this.meta,
			"cap_ro": this.cap.ro,
			"cap_rw": this.cap.rw,
			"cache_strategy": this.cache.strategy.name,
			"pending_sync": this.pending.sync,
			"pending_creation": this.pending.create,
			"pending_deletion": this.pending.delete,
		}


	# Load the data from the database into *this.
	# You should override this method in your child class to load additional data.
	async def LoadFromData(this, data):
		this.time.synced = time.time()
		this.name = data.name
		this.kind = data.kind

		try:
			this.parents = [parent.id for parent in data.parents] if data.parents else []
		except Exception as e:
			logging.debug(f"No parents set for {this.StringId()}: {e}")

		this.cap.ro = data.cap_ro
		this.cap.rw = data.cap_rw
		this.cache.strategy = CacheStrategy[data.cache_strategy]
		this.pending.sync = data.pending_sync
		this.pending.create = data.pending_creation
		this.pending.delete = data.pending_deletion
		try:
			if (isinstance(data.meta, dict)):
				this.meta.update(data.meta)
			else:
				this.meta.update(json.loads(data.meta))
		except Exception as e:
			logging.error(f"Error loading metadata for {this.StringId()}: {e}")
			pass

	
	# Hook for additional loading tasks.
	# For example, if a child stores extra variables as Ephemerals, they could load them here.
	# Will be called whenever *this is loaded from the database.
	# Override this to set other sync conditions.
	async def OnLoad(this):
		if (this.pending.create):
			await this.InitiateSync("UP")

	
	# Save the state of *this.
	# RETURNS a dictionary of the data that should be saved to the database and/or Tahoe.
	# You should override this method in your child class to save additional data.
	# Will only be called when *this has been mutated, before being Saved.
	async def Freeze(this, session=None):
		shouldDeleteSession = session is None
		if (session is None):
			session = this.executor.GetDatabaseSession()
		
		this.frozen = await this.GetDataToSave(session)
		
		if (shouldDeleteSession):
			await session.close()

		return this.frozen


	# Initiate a background task to sync *this to or from Tahoe.
	# NOTE: Only 1 sync process may be running per inode!
	# That means you cannot simultaneously upload and download.
	async def InitiateSync(this, direction="UP"):
		if (not this.sync.allowed):
			logging.debug(f"Sync not allowed of {this.StringId()}.")
			return

		logging.debug(f"Initiating sync {direction} of {this.StringId()}.")

		syncState = await this.GetState('sync')
		if (syncState == ProcessState.PENDING):
			this.pending.sync = False # Not stored in the database until the sync is complete.
			return

		syncHost = await this.GetEphemeral('sync_host')
		syncPid = await this.GetEphemeral('sync_pid')

		if (syncState == ProcessState.RUNNING):
			if (syncPid):
				try:
					if (socket.gethostname() == syncHost):
						os.kill(int(syncPid), 0)
						logging.debug(f"Sync process already running for {this.StringId()} (PID: {syncPid}).")
						await this.SetEphemeral('sync_again', True)
						this.pending.sync = False
						return
					else:
						logging.debug(f"Sync process already running for {this.StringId()} (PID: {syncPid} is running on {syncHost}, but I am {os.getpid()} on {socket.gethostname()}).")
						this.pending.sync = False
						return

				except OSError:
					syncPid = None
					syncHost = None
			else:
				logging.error(f"Unable to determine sync process for {this.StringId()}.")

			this.pending.sync = False
			return

		# TODO: Handle cases where the data needs to be synced but the sync_host is not the current host
		# For example, what happens in a multi-server environment where a sync_host goes down? How would we even know?

		syncWorker = TahoeSyncWorker.UpstreamSyncWorker
		if (direction == "DOWN"):
			syncWorker = TahoeSyncWorker.DownstreamSyncWorker

		if (not syncPid or not len(syncPid)):
			await this.SetState('sync', ProcessState.PENDING)
			kwargs = this.executor.GetWorkerArgs()
			frozenData = await this.Freeze()
			kwargs.update({
				'inode_id': this.id,
				'frozen_data': frozenData,
			})
			sync_process = multiprocessing.Process(
				target=lambda: syncWorker(kwargs),
				daemon=True,
				name=f"{this.name} Sync Worker"
			)
			sync_process.start()
			this.executor.TrackWorkerProcess(sync_process, this.id)
			logging.debug(f"Sync process started for {this.StringId()} (PID: {sync_process.pid}).")
		else:
			logging.debug(f"Sync process already running for {this.StringId()} (PID: {syncPid} is running on {syncHost}, but I am {os.getpid()} on {socket.gethostname()}).")

		this.pending.sync = False

	# Hook for additional saving tasks.
	# For example, if a child needs to save additional Ephemeral data, they could save it here.
	# Will be called whenever *this is saved to the database.
	async def OnSave(this):
		pass


	# Commit the data in *this to the database.
	# You should NOT need to override this method.
	# To change the data that are saved, override GetDataToSave instead.
	#
	# The mutated parameter is used to determine if the object needs to be updated in Tahoe.
	# If *this is mutated, it will be marked as pending_sync in the database, and a new process will be spawned to sync the object to Tahoe.
	async def Save(this, mutated=True):
		if (mutated):
			this.pending.sync = True

		session = this.executor.GetDatabaseSession()

		try:
			dataToSave = await this.GetDataToSave(session)
			logging.debug(f"Saving {this.StringId()}: {str(dataToSave)}")
			query = await session.execute(select(InodeModel).where(InodeModel.id == this.id).options(
				orm.joinedload(InodeModel.parents),
				orm.joinedload(InodeModel.children)
			))
			model = query.scalar()
			for key, value in dataToSave.items():
				setattr(model, key, value)

			await session.commit()
			await session.close()
			await this.OnSave()
			await this.WasJustWrittenTo()
			logging.debug(f"{this.StringId()} updated in the database.")

			if (mutated
				and (
					(this.sync.when.mutated)
					or (this.sync.when.deleted and this.pending.delete)
				)
			):
				await this.InitiateSync("UP")

		except NoResultFound as e:
			logging.error(f"{this.StringId()} not found in the database.")
			raise ValueError(f"{this.StringId()} does not exist in the database.")


	# Anything you'd like to do before *this is synced to Tahoe.
	# Will be called by TahoeSyncWorker.PushUpstreamToSource.
	# Should ONLY operate on this.frozen data
	async def BeforePushUpstream(this):
		logging.debug(f"Pending operations for {this.StringId()}: {str(dict(this.pending))}")

	# Update some data in the source (i.e. Tahoe).
	# Please override for your child class.
	# Will be called by TahoeSyncWorker.PushUpstreamToSource.
	# Should ONLY operate on this.frozen data
	async def PushUpstream(this):
		pass

	# Anything you'd like to do after *this is synced to Tahoe.
	# Will be called by TahoeSyncWorker.PushUpstreamToSource.
	# Should ONLY operate on this.frozen data
	async def AfterPushUpstream(this):
		if (this.pending.delete or await this.GetState('delete') in [ProcessState.COMPLETE, ProcessState.ERROR]):
			logging.debug(f"{this.StringId()} has been deleted; no further changes will be made.")
			return

		this.pending.sync = False
		this.pending.create = False
		# NOTE: deletion is one way. Once it's deleted, it's gone.
		session = this.executor.GetDatabaseSession()
		query = await session.execute(select(InodeModel).where(InodeModel.id == this.id))
		model = query.scalar()
		model.pending_sync = False
		model.pending_creation = False
		model.last_accessed = time.time()
		await session.commit()
		await this.WasJustWrittenTo()
		await session.close()


	# Anything you'd like to do before *this is synced from Tahoe.
	# Will be called by TahoeSyncWorker.PullDownstreamFromSource.
	#NOTE: DO NOT CALL Save() HERE! (it will be done for you after all Pulling is done)
	async def BeforePullDownstream(this):
		pass
	
	# Update our local cache with data from Tahoe.
	# Please override for your child class.	
	# Will be called by TahoeSyncWorker.PullDownstreamFromSource.
	#NOTE: DO NOT CALL Save() HERE! (it will be done for you after all Pulling is done)
	async def PullDownstream(this):
		pass
	
	# Anything you'd like to do after *this is synced from Tahoe.
	# Will be called by TahoeSyncWorker.PullDownstreamFromSource.
	#NOTE: DO NOT CALL Save() HERE! (it will be done for you after all Pulling is done)
	async def AfterPullDownstream(this):
		this.pending.sync = False
		this.time.retrieved = time.time()
		session = this.executor.GetDatabaseSession()
		query = await session.execute(select(InodeModel).where(InodeModel.id == this.id))
		model = query.scalar()
		model.pending_sync = False
		model.last_accessed = time.time()
		await session.commit()
		await this.WasJustWrittenTo()
		await session.close()


	async def GetParentPath(this):
		if (this.executor.strategy.storage == StorageStrategy.MIRROR):
			parent = await this.GetParent()
			if (parent is None or parent.cap.rw is None):
				logging.error(f"Parent of {this.StringId()} not found or has no Tahoe capability.")
				raise IOError(errno.ENOENT, f"Parent of {this.StringId()} not found or has no Tahoe capability.")
			path = parent.cap.rw + "/" + os.path.basename(this.upath)

		elif (this.executor.strategy.storage == StorageStrategy.FLAT):
				path = this.executor.rootcap + "/" + str(this.id)

		else:
			logging.error(f"Storage strategy {this.executor.strategy.storage} not implemented.")
			raise NotImplementedError(f"Storage strategy {this.executor.strategy.storage} not implemented.")

		return path


	async def UploadToTahoe(this, cap):
		logging.error(f"UploadToTahoe not implemented for {this.StringId()}.")


	# Where on the disk should *this store its data?
	def GetPathToCacheOnDisk(this):
		return this.executor.cache_dir.joinpath(this.upath).resolve()


	async def CommonWrite(this, path):
		await this.SetState('write', ProcessState.RUNNING)

		try:
			logging.debug(f"Uploading {this.StringId()} to Tahoe.")
			uploadPath = path
			if (this.cap.rw is not None):
				uploadPath = this.cap.rw
			try:
				uploadResponse = await this.UploadToTahoe(uploadPath)
			except Exception as e:
				logging.error(f"Error uploading {this.StringId()} to Tahoe: {e}")
				await this.SetState('write', ProcessState.ERROR)
				return

			rwCap = str(await uploadResponse.text())
			uploadResponse.close()
			if (this.cap.rw is None or this.cap.rw != rwCap):
				this.cap.rw = rwCap
				session = this.executor.GetDatabaseSession()
				query = await session.execute(select(InodeModel).where(InodeModel.id == this.id))
				model = query.scalar()
				model.cap_rw = this.cap.rw
				await session.commit()

				# This is done in AfterPushUpstream and currently this method is only called by PushUpstream
				# await this.WasJustWrittenTo()

				await session.close()
				# logging.debug(f"Uploaded {this.StringId()} to Tahoe: {this.cap.rw}")

			await this.SetState('write', ProcessState.COMPLETE)
			logging.debug(f"{this.StringId()} uploaded successfully.")

		except Exception as e:
			await this.SetState('write', ProcessState.ERROR)
			logging.error(f"Error uploading {this.StringId()} to Tahoe: {e}")
			raise IOError(errno.EREMOTEIO, f"PushUpstream error for file {this.upath}")


	# Helper method to delete an Inode from the database and cache.
	async def CommonDelete(this, stages=None, path=None):
		await this.SetState('delete', ProcessState.RUNNING)
		try:
			tahoe = this.executor.GetSourceConnection()

			if (stages is None):
				stages = [
					Stage.TAHOE,
					Stage.DATABASE,
					Stage.CACHE,
				]

			if (Stage.TAHOE in stages and path is not None):
				logging.debug(f"Deleting {this.StringId()} from Tahoe.")
				try:
					deleteResponse = await tahoe.Delete(path, iscap=True)
				except aiohttp.ClientResponseError as e:
					if (e.status in [404, 410]):
						pass
					else:
						logging.error(f"Error deleting {this.StringId()} from Tahoe: {e}")
						await this.SetState('delete', ProcessState.ERROR)
						return

			if (Stage.DATABASE in stages):
				logging.debug(f"Deleting {this.StringId()} from the database.")
				session = this.executor.GetDatabaseSession()
				query = await session.execute(select(InodeModel).where(InodeModel.id == this.id))
				model = query.scalar()
				await session.delete(model)
				await session.commit()
				await session.close()

			if (Stage.CACHE in stages):
				logging.debug(f"Deleting {this.StringId()} from cache.")
				await this.executor.PurgeCachedInode(this)

			await this.SetState('delete', ProcessState.COMPLETE)
			logging.debug(f"{this.__class__.__name__} {this.upath} deleted successfully.")

		except Exception as e:
			await this.SetState('delete', ProcessState.ERROR)
			eons.util.LogStack()
			logging.error(f"Error deleting {this.StringId()}: {e}")
			raise e


	# Update the Inode's upath and parent.
	async def CommonMove(this, dest_upath):
		oldParent = None
		try:
			oldParent = await this.GetParent()
			await oldParent.RemoveChild(this)
		except Exception as e:
			logging.debug(f"Could not remove {this.StringId()} from parent: {e}")

		this.upath = dest_upath # Changes our parent.
		this.name = os.path.basename(dest_upath)
		session = this.executor.GetDatabaseSession()
		query = await session.execute(select(InodeModel).where(InodeModel.id == this.id))
		model = query.scalar()
		model.upath = this.upath
		model.name = this.name
		await session.commit()
		await session.close()

		await this.executor.PurgeCachedInode(this)

		# oldParent will be None if the parent was moved and we're just updating our upath to match the new structure.
		if (oldParent is not None):
			newParent = await this.GetParent()
			this.parents = [p for p in this.parents if p != oldParent.id]
			this.parents.append(newParent.id)
			await this.Save(mutated=False)
			await newParent.AddChild(this)
			await this.executor.PurgeCachedInode(newParent)

		await this.WasJustWrittenTo() # Update the last written time, regardless of if we saved *this or not.


	# Helper function to check if a given upath is a particular type of Inode.
	async def IsInode(this, cls, upath):
		destExists = None
		try:
			destExists = await cls.From(
				executor=this.executor,
				upath=upath,
				createIfNotExists=False,
				allowSync=this.sync.allowed,
			)
			return destExists is not None
		except Exception:
			return False


	# Helper function to throw an error if a given upath is a particular type of Inode.
	async def RequireInodeIsNot(this, cls, upath):
		destExists = await this.IsInode(cls, upath)
		if (destExists):
			raise IOError(errno.EEXIST, f"{upath} already exists and is a {cls.__name__}.")


	###############################################################################################
	# Callable filesystem methods
	###############################################################################################

	async def Access(this, mode):
		await this.Accessed()
		return True

	async def Open(this, flags=0):
		logging.info(f"{this.StringId()} Open({flags}) called.")
		await this.Accessed()

		if (flags & os.O_RDWR):
			await this.SetState('write', ProcessState.RUNNING)
			# Will prevent a sync from running but will not stop an active one.

		elif (flags & os.O_WRONLY):
			await this.SetState('write', ProcessState.RUNNING)
			# Will prevent a sync from running but will not stop an active one.

		elif (flags & os.O_RDONLY):
			await this.SetState('read', ProcessState.RUNNING)
		
		return True

	async def Close(this):
		logging.info(f"{this.StringId()} Close() called.")
		await this.SetState('read', ProcessState.IDLE)
		await this.SetState('write', ProcessState.IDLE)
		return True

	async def Chmod(this, mode):
		logging.info(f"{this.StringId()} Chmod({mode}) called.")
		this.meta['mode'] = mode
		await this.Save(mutated=False)
		return True

	async def Chown(this, uid, gid):
		logging.info(f"{this.StringId()} Chown({uid}, {gid}) called.")
		this.meta['uid'] = uid
		this.meta['gid'] = gid
		await this.Save(mutated=False)
		return True

	async def Utime(this, atime, mtime):
		this.meta['atime'] = atime
		this.meta['mtime'] = mtime
		await this.Save(mutated=False)
		return True

	async def Utimens(this, atime_ns, mtime_ns):
		this.meta['atime_ns'] = atime_ns
		this.meta['mtime_ns'] = mtime_ns
		await this.Save(mutated=False)
		return True

	async def Ioctl(this, command, args):
		logging.info(f"Ioctl command {command} with args {args} on {this.StringId()}")
		return None

	# Map a file block to a device‐specific block. Typically used
	# by cluster or block device filesystems. Tahoe FS does not
	# operate at the block layer, so we can simply say “unsupported.”

	# :param blocksize: The block size for which we want a mapping
	# :return: The mapped block index or ENOSYS if not supported
	async def Bmap(this, blocksize):
		logging.debug(f"{this.StringId()} Bmap(blocksize={blocksize})")
		raise IOError(errno.ENOSYS, "bmap not supported")

	async def Move(this, dest_upath):
		raise IOError(errno.ENOSYS, "move not supported on undifferentiated Inodes")

	async def Copy(this, dest_upath):
		raise IOError(errno.ENOSYS, "copy not supported on undifferentiated Inodes")

	async def GetXAttr(this, name):
		if (this.meta and 'xattr' in this.meta and name in this.meta['xattr']):
			return this.meta['xattr'][name]
		return None

	async def SetXAttr(this, name, value):
		logging.info(f"{this.StringId()} SetXAttr({name}, {value}) called.")
		if ('xattr' not in this.meta):
			this.meta['xattr'] = {}
		this.meta['xattr'][name] = value
		await this.Save(mutated=False)
		return True

	async def RemoveXAttr(this, name):
		logging.info(f"{this.StringId()} RemoveXAttr({name}) called.")
		if (this.meta and 'xattr' in this.meta and name in this.meta['xattr']):
			del this.meta['xattr'][name]
			await this.Save(mutated=False)
			return True
		return False

	async def ListXAttr(this):
		if (this.meta and 'xattr' in this.meta):
			return list(this.meta['xattr'].keys())
		return []

	async def Poll(this):
		return {}

	async def GetAttr(this):
		ret = {}
		for attr in ['mode', 'uid', 'gid', 'atime', 'mtime', 'ctime', 'atime_ns', 'mtime_ns']:
			try:
				ret[attr] = this.meta[attr]
			except KeyError:
				ret[attr] = None
		return ret

	async def Unlink(this):
		logging.info(f"{this.StringId()} Unlink() called.")
		if (this.upath == ""):
			raise IOError(errno.EACCES, "cannot unlink root directory")

		# FIXME: This should work for now, but we do need to handle multiple parents some day.
		parent = await this.GetParent()
		await parent.RemoveChild(this)

		this.parents = [p for p in this.parents if p != parent.id]

		# signal to run sync immediately
		# NOTE: This is one way - the delete state should never go back to IDLE.
		await this.SetState('delete', ProcessState.PENDING)

		this.pending.delete = True
		await this.Save(mutated=True)


	# Create a new 'special' file (block device, char device, etc.).
	# In many FUSE filesystems, mknod is used for creating:
	# 	- FIFOs
	# 	- Character devices
	# 	- Block devices
	# But in a Tahoe-based FS, we often do not support these.
	
	# :param mode: The filesystem mode (e.g. S_IFREG, S_IFCHR, S_IFBLK).
	# :param dev:  Device number (only relevant for device nodes).
	# :raises: Typically returns an error if not supported, or 0 if successful.
	async def Mknod(this, mode, dev=0):
		logging.info(f"{this.StringId()} Mknod({mode}, dev={dev}) called.")
		raise IOError(errno.ENOSYS, "mknod not supported in TruckeeFS")


	# Create a hard link from `target` to this inode's upath.
	# Hard links typically require referencing the same underlying data.
	# Tahoe doesn't truly allow for standard OS-level hard links.
	
	# :param target: The existing file whose data we want to link to.
	# :raises: Typically returns ENOSYS or 0.
	async def Link(this, target):
		logging.info(f"{this.StringId()} Link(target={target}) called.")
		raise IOError(errno.ENOSYS, "link not supported in TruckeeFS")


	# Create a symbolic link named 'this.upath' which points to `target`.
	# In a typical local filesystem, we store 'target' as link content.
	# In Tahoe, there is no direct concept of symlinks, so we often
	# do not support them natively.
	
	# :param target: The path this symlink should point to.
	# :raises: Typically returns ENOSYS or 0.
	async def Symlink(this, target):
		logging.info(f"{this.StringId()} Symlink(target={target}) called.")
		raise IOError(errno.ENOSYS, "symlink not supported in TruckeeFS")


	# Read the target of a symlink. If this is not a symlink, or if
	# symlinks aren't supported, return an error.
	
	# :return: The target path of the symlink, as a string.
	# :raises: ENOENT if not a link, or ENOSYS if symlinks not supported.
	async def ReadLink(this):
		logging.debug(f"{this.StringId()} ReadLink() called.")
		raise IOError(errno.ENOSYS, "readlink not supported in TruckeeFS")


class FileOnDisk:
	# HEADER_FORMAT: 4-byte magic, 4-byte reserved, 8-byte data size (total 16 bytes)
	HEADER_FORMAT = '<4s4sQ'
	# HEADER_SIZE: computed size of the header (16 bytes)
	HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
	# MAGIC: identifier for the file format
	MAGIC = b'FOD0'

	# Initialize the FileOnDisk instance.
	# Mode must be one of: 'rb' (read-only), 'r+b' (read/write), or 'w+b' (new file).
	def __init__(this, path, mode='r+b', key=None):
		if (mode not in ('rb', 'r+b', 'w+b')):
			raise IOError(errno.EACCES, f"Unsupported mode {mode!r}")
		
		this.path = path
		this.mode = mode
		this.data_size = 0
		this.fp = None  # Will hold the aiofiles file handle

	# Open the file asynchronously.
	# In 'w+b' mode, a new file is created with an initial header.
	# In 'rb' or 'r+b' modes, the header is read and validated.
	async def Open(this):
		logging.debug(f"Opening file {this.path} in mode {this.mode}")
		try:
			this.fp = await aiofiles.open(this.path, mode=this.mode)
		except FileNotFoundError as e:
			if (this.mode in ('rb', 'r+b')):
				logging.error(f"File {this.path} not found")
				raise e
			elif (this.mode == 'w+b'):
				logging.info(f"Creating new file {this.path} with parents.")
				Path(this.path).parent.mkdir(parents=True, exist_ok=True)
				this.fp = await aiofiles.open(this.path, mode=this.mode)
		except Exception as e:
			logging.error(f"Error opening file {this.path}: {e}")
			raise e

		if (this.mode in ('rb', 'r+b')):
			# Read and validate the header.
			await this.fp.seek(0)
			header_data = await this.fp.read(this.HEADER_SIZE)
			if (len(header_data) != this.HEADER_SIZE):
				await this.fp.close()
				raise ValueError("Invalid header data in file")
			magic, reserved, data_size = struct.unpack(this.HEADER_FORMAT, header_data)
			if (magic != this.MAGIC):
				await this.fp.close()
				raise ValueError("Invalid file format (magic mismatch)")
			this.data_size = data_size
		else:  # 'w+b' mode: create a new file with empty data.
			this.data_size = 0
			await this.WriteHeaderRaw()

	def IsOpen(this):
		return this.fp is not None

	# Write the header (magic, reserved, data_size) to the file.
	async def WriteHeaderRaw(this):
		header = struct.pack(this.HEADER_FORMAT, this.MAGIC, b'\x00' * 4, this.data_size)
		await this.fp.seek(0)
		await this.fp.write(header)
		await this.fp.flush()

	# Asynchronously write the header.
	async def WriteHeader(this):
		await this.WriteHeaderRaw()

	# Asynchronously read data (excluding the header) starting at the given offset.
	# If size is None, the read continues until the end of the file.
	# Returns the read bytes.
	async def Read(this, offset=0, size=None):
		logging.debug(f"Reading {size} bytes at offset {offset} from {this.path}")
		if (offset < 0 or offset > this.data_size):
			return b""
		if (size is None):
			size = this.data_size - offset
		start = this.HEADER_SIZE + offset
		await this.fp.seek(start)
		return await this.fp.read(size)

	# Asynchronously write data to the file at the specified offset.
	# If needed, resize the file before writing.
	# The header is updated with the new data_size.
	# Returns the number of bytes written.
	async def Write(this, data, offset=0):
		logging.debug(f"Writing {len(data)} bytes at offset {offset} to {this.path}")
		new_end = offset + len(data)
		if (new_end > this.data_size):
			await this._Resize(new_end)
		start = this.HEADER_SIZE + offset
		await this.fp.seek(start)
		await this.fp.write(data)
		this.data_size = max(this.data_size, new_end)
		# Update header with new data_size.
		header = struct.pack(this.HEADER_FORMAT, this.MAGIC, b'\x00' * 4, this.data_size)
		await this.fp.seek(0)
		await this.fp.write(header)
		await this.fp.flush()
		return len(data)

	# Asynchronously resize the file (excluding the header) to accommodate new_data_size.
	# Uses aiofiles.os.truncate to change the file size.
	async def _Resize(this, new_data_size):
		logging.debug(f"Resizing {this.path} to {new_data_size} bytes")
		new_total_size = this.HEADER_SIZE + new_data_size
		await this.fp.flush()
		await asyncio.to_thread(os.truncate, this.path, new_total_size)
		this.data_size = new_data_size

	# Asynchronously truncate the file (excluding header) to the specified size.
	# Updates the header with the new data_size.
	# Returns True upon success.
	async def Truncate(this, size):
		logging.debug(f"Truncating {this.path} to {size} bytes")
		new_total_size = this.HEADER_SIZE + size
		await this.fp.flush()
		await asyncio.to_thread(os.truncate, this.path, new_total_size)
		this.data_size = size
		header = struct.pack(this.HEADER_FORMAT, this.MAGIC, b'\x00' * 4, this.data_size)
		await this.fp.seek(0)
		await this.fp.write(header)
		await this.fp.flush()
		return True

	async def Rename(this, newPath):
		oldPath = this.path
		if (oldPath == newPath):
			logging.debug(f"Nop Rename: {oldPath} → {newPath}")
			return

		logging.info(f"Renaming cache file {oldPath} → {newPath}")

		# 1) flush + fsync
		if (this.fp):
			try:
				await this.fp.flush()
				await asyncio.to_thread(os.fsync, this.fp._file.fileno()) # just to be super extra certain
			except Exception as e:
				logging.warning(f"Flush/fsync before rename failed: {e}")

		# 2) close the handle
		if (this.fp):
			try:
				await this.fp.close()
			except Exception as e:
				logging.warning(f"Error closing file before rename: {e}")
			finally:
				this.fp = None

		# 3) ensure parent dir
		newPath.parent.mkdir(parents=True, exist_ok=True)

		# 4) attempt atomic rename, fallback to copy+unlink on cross‐device
		try:
			await aiofiles.os.rename(oldPath, newPath)
		except OSError as e:
			logging.warning(f"`aiofiles.os.rename` failed ({e}); falling back to copy2+unlink")
			# copy2 preserves metadata; still run in thread
			await asyncio.to_thread(shutil.copy2, oldPath, newPath)
			await asyncio.to_thread(os.remove, oldPath)

		# 5) update internal state
		this.path = newPath

		# 6) reopen in r+b, revalidate header matches data_size
		this.mode = 'r+b'
		await this.Open()


	# Asynchronously flush any pending changes to disk and update the header.
	async def Flush(this):
		logging.debug(f"Flushing file {this.path}")
		await this.fp.flush()
		await this.WriteHeader()
		await asyncio.to_thread(os.fsync, this.fp._file.fileno()) # just to be super extra certain

	# Asynchronously flush and close the file.
	async def Close(this):
		logging.debug(f"Closing file {this.path}")
		if (not this.fp):
			return
		await this.fp.flush()
		await asyncio.to_thread(os.fsync, this.fp._file.fileno()) # unnecessary, but just in case
		await this.fp.close()
		this.fp = None

	# Async context manager entry: opens the file.
	async def __aenter__(this):
		await this.Open()
		return this

	# Async context manager exit: ensures the file is closed.
	async def __aexit__(this, exc_type, exc_val, exc_tb):
		await this.Close()
		return False


class File(Inode):
	defaultPermissions = 0o644

	def __init__(
		this,
		upath="",
		name=None,
		meta=None,
	):
		if (meta is None):
			meta = {
				'size': 0
			}

		super().__init__(upath, name, meta)
		this.pending.download = False
		this.pending.upload = False

		# Actual cache file will only be initialized when From() is called.
		this.data = None


	async def InitializeEphemerals(this):
		await super().InitializeEphemerals()
		await this.SetEphemeral("pending_download", this.pending.download)
		await this.SetEphemeral("pending_upload", this.pending.upload)


	async def GetDataToSave(this, session):
		ret = await super().GetDataToSave(session)
		ret.update({
			# Save the file path (from the FileOnDisk object) in our metadata.
			'data': this.data.path if this.data else None
		})
		return ret


	async def LoadFromData(this, data):
		await super().LoadFromData(data)
		this.data = data.data
		# OnLoad will actually open the file.


	async def CreateCacheFile(this):
		if (this.data is not None):
			logging.warning(f"Cache {this.StringId()} already exists at {this.GetPathToCacheOnDisk()}. Will not truncate.")
			return
		logging.debug(f"Creating cache {this.StringId()} at {this.GetPathToCacheOnDisk()}")
		this.GetPathToCacheOnDisk().parent.mkdir(parents=True, exist_ok=True)
		this.data = FileOnDisk(this.GetPathToCacheOnDisk(), mode='w+b')
		await this.data.Open()
		this.data.mode = 'r+b' # Set the mode to read/write after creating the file, just in case Open is called again.


	# Try, by whatever means necessary, to open this.data from the local file cache.
	async def LoadData(this):
		# This occurred during testing, so we'll watch for it; though it may be an extraneous check.
		if (this.pending.delete and this.data is None):
			# We're in a weird state. Let's investigate.
			deleteState = this.GetState('delete')
			if (deleteState in [ProcessState.PENDING, ProcessState.RUNNING]):
				logging.warning(f"{this.StringId()} is pending deletion")
				# But that's fine. Maybe the deletion process needed to do an extra lookup.
			elif (deleteState == ProcessState.COMPLETE):
				logging.error(f"{this.StringId()} is marked for deletion but has no data. Perhaps it was already deleted?")
				raise IOError(errno.ENOENT, f"{this.StringId()} is marked for deletion but has no data.")
			# Otherwise we'll just let it go; there's nothing we should be doing about it here.

		this.pending.download = await this.GetEphemeral("pending_download", coerceType=bool)
		this.pending.upload = await this.GetEphemeral("pending_upload", coerceType=bool)

		# Try to get the file from cache.
		if (isinstance(this.data, str)):
			try:
				filePath = this.data
				this.data = FileOnDisk(filePath, mode='r+b')
				logging.debug(f"Got cache {this.StringId()} at {filePath}")
			except:
				logging.error(f"Error loading cache {this.StringId()} at {this.data}")
				this.data = None

		if (this.data is not None):
			if (not this.data.IsOpen()):
				try:
					await this.data.Open()
				except Exception as e:
					logging.debug(f"Stale cache found for {this.StringId()}: {e}")
					this.data = None

		if (this.data is None):
			if (this.pending.create):
				await this.CreateCacheFile()
				await this.SetEphemeral('pending_upload', True)
				await this.SetState('write', ProcessState.PENDING)
			else:
				if (this.pending.upload):
					raise IOError(errno.ENOENT, f"{this.StringId()} not found in cache but should be uploaded.")

				tahoe = this.executor.GetSourceConnection()
				path = await this.GetParentPath()
				try:
					response = await tahoe.Head(path, iscap=True)
					if (response.status == 200):
						this.pending.sync = True # NOTE: this is not synced to the database, but that should be okay here.
						await this.SetEphemeral('pending_download', True)
						logging.debug(f"{this.StringId()} found in Tahoe; will download.")

				except Exception as e:
					logging.error(f"Error checking {this.StringId()} in Tahoe: {e}")
					raise IOError(errno.ENOENT, f"Error checking {this.StringId()} in Tahoe")

			# Refresh cached ephemerals
			this.pending.download = await this.GetEphemeral("pending_download", coerceType=bool)
			this.pending.upload = await this.GetEphemeral("pending_upload", coerceType=bool)

		if (this.data is not None):
			if (not this.data.IsOpen()):
				try:
					await this.data.Open()
				except Exception as e:
					logging.debug(f"Error opening {this.StringId()}: {e}")
					raise e

		if (this.pending.sync):
			if (this.pending.download is not None and this.pending.download):
				await this.InitiateSync("DOWN")
			elif (this.pending.upload is not None and this.pending.upload):
				await this.InitiateSync("UP")
			elif (this.pending.create or this.pending.delete):
				await this.InitiateSync("UP")
			else:
				logging.warning(f"{this.StringId()} has pending sync but no direction. Ignoring.")


	async def OnLoad(this):
		# Explicitly DO NOT call super().OnLoad()
		await this.LoadData()


	async def OnSave(this):
		if (not this.pending.download):
			this.pending.upload = True

		await this.SetEphemeral("pending_download", this.pending.download)
		await this.SetEphemeral("pending_upload", this.pending.upload)


	async def RequireOpenData(this):
		if (this.data is None):
			logging.error(f"{this.StringId()} has no data to open.")
			raise IOError(errno.EIO, f"{this.StringId()} has no data to open.")

		if (not this.data.IsOpen()):
			try:
				this.data.mode = 'r+b'
				await this.data.Open()
			except Exception as e:
				logging.error(f"Error opening {this.StringId()}: {e}")
				raise IOError(errno.EIO, f"Error opening {this.StringId()}")


	async def UploadToTahoe(this, cap):
		tahoe = this.executor.GetSourceConnection()
		await this.RequireOpenData()
		uploadRequestData = await this.data.Read(0, this.data.data_size)
		uploadResponse = await tahoe.Put(cap, data=uploadRequestData, iscap=True)
		return uploadResponse


	async def CommonDelete(this, stages=None, path=None):
		await super().CommonDelete(stages, path)

		if (this.data is not None):
			try:
				logging.debug(f"Deleting {this.StringId()} from the filesystem at {this.data.path}")
				await this.data.Close()
				os.remove(this.data.path)
			except Exception as e:
				logging.error(f"Error deleting {this.StringId()}: {e}")
				raise IOError(errno.EIO, f"Error deleting {this.StringId()}")


	# Prepare file for upload by flushing and checking consistency.
	async def BeforePushUpstream(this):
		await super().BeforePushUpstream()

		if (this.pending.delete and this.data is None):
			return

		try:
			if (this.data.IsOpen()):
				await this.data.Flush()
			else:
				await this.data.Open()

			logging.debug(f"BeforePushUpstream: {this.StringId()} flushed successfully.")
		except Exception as e:
			logging.error(f"BeforePushUpstream error for {this.StringId()}: {str(e)}")
			raise IOError(errno.EFAULT, f"BeforePushUpstream error for {this.StringId()}")

	# Upload the file's data to Tahoe and return the remote capability.
	async def PushUpstream(this):
		await super().PushUpstream()
		path = await this.GetParentPath()

		logging.debug(f"{this.StringId()} is syncing upstream: PUT: {this.pending.upload or this.pending.create}, DELETE: {this.pending.delete}")
		if (this.pending.upload or this.pending.create):
			if (this.pending.delete):
				logging.debug(f"{this.StringId()} is marked for both creation and deletion. Deleting.")
				if (this.pending.upload):
					await this.CommonDelete(path=path) # include tahoe
				else:
					await this.CommonDelete() # skip tahoe
				return

			await this.CommonWrite(path)

		elif (this.pending.delete):
			await this.CommonDelete(path=path)

	async def AfterPushUpstream(this):
		await super().AfterPushUpstream()
		this.pending.upload = False
		this.pending.download = False
		await this.SetEphemeral("pending_upload", False)
		await this.SetEphemeral("pending_download", False)


	# Download the file from Tahoe and update the local cache.
	# NOTE: DO NOT CALL Save() HERE! (it will be done for you after all Pulling is done)
	async def PullDownstream(this):
		await super().PullDownstream()
		tahoe = this.executor.GetSourceConnection()
		path = await this.GetParentPath()

		if (this.pending.download):
			try:
				if (this.data is None):
					await this.CreateCacheFile()

				# Download the file from Tahoe.
				downloadResponse = await tahoe.Get(path, iscap=True)
				data = await downloadResponse.read()
				await this.data.Write(data)
				downloadResponse.close()
				logging.debug(f"PullDownstream: {this.StringId()} downloaded successfully.")
			
			except Exception as e:
				logging.error(f"PullDownstream error for {this.StringId()}: {str(e)}")
				raise IOError(errno.EREMOTEIO, f"PullDownstream error for {this.StringId()}")

	async def AfterPullDownstream(this):
		await super().AfterPullDownstream()
		this.pending.download = False
		await this.SetEphemeral("pending_download", False)


	# Any method that would trigger Accessed will rely on *this having valid data, so let's tell them to back off if it's not ready.
	async def Accessed(this, save=True):
		if (this.pending.download):
			this.pending.download = await this.GetEphemeral("pending_download", coerceType=bool)
			if (this.pending.download): # just to make sure
				raise IOError(errno.EAGAIN, "File is still downloading")
		try:
			await this.RequireOpenData()
		except Exception as e:
			await this.LoadData()
			await this.RequireOpenData()
		return await super().Accessed(save)


	# Get the Inode for the file to clobber, if it exists
	async def GetFileToClobber(this, destination):
		clobberee = None
		try:
			clobberee = await File.From(
				executor=this.executor,
				upath=destination,
				createIfNotExists=False,
				allowSync=this.sync.allowed,
			)
			if (clobberee):
				await clobberee.data.Close()
		except Exception as e:
			logging.debug(f"{this.StringId()} cannot clobber {destination}: {e}")

		if (clobberee is not None):
			logging.debug(f"{this.StringId()} will clobber {clobberee.StringId()}")
		return clobberee


	###############################################################################################
	# Callable filesystem methods
	###############################################################################################

	async def GetAttr(this):
		attrs = await super().GetAttr()
		await this.Accessed(save=False)
		attrs["size"] = this.data.data_size
		return attrs

	async def Open(this, flags):
		logging.info(f"Opening {this.StringId()} with flags {flags}")
		ret = await super().Open(flags)
		if (flags & os.O_TRUNC):
			await this.Truncate(0)
		return ret

	async def Close(this):
		logging.info(f"Closing {this.StringId()}")
		ret = await super().Close()
		if (this.data is not None and not this.data.IsOpen()):
			await this.data.Close()
		return ret

	# Read data from the file at the given offset.
	async def Read(this, offset, size):
		logging.info(f"Reading {this.StringId()} at offset {offset} with size {size}")
		await this.Accessed()
		return await this.data.Read(offset, size)

	# Write data to the file at the given offset.
	async def Write(this, offset, data):
		logging.info(f"Writing {this.StringId()} at offset {offset} with size {len(data)}")
		await this.Accessed(save=False)
		bytes_written = await this.data.Write(data, offset)
		this.pending.upload = True
		await this.Save(mutated=True)
		return bytes_written

	# Truncate the file to the specified size.
	async def Truncate(this, size):
		logging.info(f"Truncating {this.StringId()} to size {size}")
		await this.Accessed(save=False)
		await this.data.Truncate(size)
		this.pending.upload = True
		await this.Save(mutated=True)
		return True

	# Append data to the end of the file.
	async def Append(this, data):
		logging.info(f"Appending to {this.StringId()} with size {len(data)}")
		await this.Accessed(save=False)
		offset = this.data.data_size
		bytes_written = await this.data.Write(data, offset)
		this.pending.upload = True
		await this.Save(mutated=True)
		return bytes_written

	async def Flush(this):
		logging.info(f"Flushing {this.StringId()}")
		await this.Accessed(save=False)
		await this.data.Flush()
		return True

	# Copy this file to a new destination.
	async def Copy(this, dest_upath):
		logging.info(f"Copying {this.StringId()} to {dest_upath}")
		await this.RequireInodeIsNot(Directory, dest_upath)
		await this.Accessed(save=False)
		await this.data.Flush()

		clobberee = await this.GetFileToClobber(dest_upath)

		# Copy the underlying cached file.
		newFilePath = this.executor.cache_dir.joinpath(dest_upath).resolve()
		newFilePath.parent.mkdir(parents=True, exist_ok=True)
		try:
			copy2(this.data.path, newFilePath)
		except Exception as e:
			logging.error(f"Error copying {this.StringId()} to {newFilePath}: {e}")
			raise IOError(errno.EIO, f"Error copying {this.StringId()} to {newFilePath}")

		if (clobberee):
			clobberee.data = FileOnDisk(newFilePath, mode='r+b')
			await clobberee.data.Open()
			clobberee.meta.update(this.meta)
			await clobberee.Save(mutated=True)
			return clobberee

		# Create a new Inode for the copied file.
		newFile = await File.From(
			executor=this.executor,
			upath=dest_upath,
			createIfNotExists=True,
			meta=this.meta.copy(),
			allowSync=this.sync.allowed,
		)
		return newFile

	# Move this file to a new destination.
	async def Move(this, dest_upath):
		logging.info(f"Moving {this.StringId()} to {dest_upath}")
		await this.RequireInodeIsNot(Directory, dest_upath)
		await this.Accessed(save=False)

		clobberee = await this.GetFileToClobber(dest_upath)

		# Move the underlying cached file.
		# NOTE: This does not require an upload because the file is not changing.
		newFilePath = this.executor.cache_dir.joinpath(dest_upath).resolve()
		logging.debug(f"New file path for {this.StringId()} is {newFilePath}")

		# Move the underlying cache file.
		await this.data.Rename(newFilePath)

		if (clobberee):
			await this.data.Close()
			clobberee.data = FileOnDisk(newFilePath, mode='r+b')
			await clobberee.data.Open()
			clobberee.meta.update(this.meta)
			await clobberee.Save(mutated=True)
			await this.executor.PurgeCachedInode(clobberee)

			# delete *this
			await this.SetState('delete', ProcessState.PENDING)
			this.pending.delete = True
			await this.Save(mutated=True)
			await this.executor.PurgeCachedInode(this)

			return clobberee

		# Also make sure we immediately update the database with the new file location
		session = this.executor.GetDatabaseSession()
		query = await session.execute(select(InodeModel).where(InodeModel.id == this.id))
		model = query.scalar()
		model.data = newFilePath
		await session.commit()
		await session.close()

		await this.CommonMove(dest_upath)
		return this


class Directory(Inode):
	defaultPermissions = 0o755

	def __init__(this, upath="", name="Directory"):
		super().__init__(upath, name)

		this.sync.when.mutated = False

		this.children = []  # List of child ids.


	async def GetDataToSave(this, session):
		ret = await super().GetDataToSave(session)
		
		query = await session.execute(select(InodeModel).where(InodeModel.id.in_(this.children)))
		childList = query.scalars().all()

		ret.update({
			'children': childList
		})
		if (this.executor.strategy.storage == StorageStrategy.FLAT):
			ret.update({
				'pending_sync': False,  # Directories do not sync in flat storage.
			})
		return ret


	async def OnSave(this):
		await super().OnSave()

		# Directories don't need any special creation logic when using flat storage.
		if (this.pending.create and this.executor.strategy.storage == StorageStrategy.FLAT):
			this.pending.create = False
			session = this.executor.GetDatabaseSession()
			query = await session.execute(select(InodeModel).where(InodeModel.id == this.id))
			model = query.scalar()
			model.pending_creation = False
			await session.commit()
			await session.close()


	async def LoadFromData(this, data):
		await super().LoadFromData(data)
		try:
			this.children = [child.id for child in data.children] if data.children else []
		except Exception as e:
			logging.debug(f"No children loaded for {this.StringId()}: {e}")
			this.children = []



	async def UploadToTahoe(this, cap):
		tahoe = this.executor.GetSourceConnection()
		if (this.cap.rw is not None):
			logging.error(f"Directories can only be created, we do not write to them. {cap} will be ignored. {this.StringId()} will not be written.")
			return

		createRequestData = {
			"t": "mkdir",
			"name": os.path.basename(this.upath)
		}
		createResponse = await tahoe.Post(cap, createRequestData, iscap=True)
		return createResponse


	async def PushUpstream(this):
		await super().PushUpstream()
		tahoe = this.executor.GetSourceConnection()		

		if (this.pending.create):
			if (this.pending.delete):
				if (this.upath == '' or this.upath == '/'):
					logging.error(f"Trying to both create and delete the root directory. Ignoring.")
					raise IOError(errno.EINVAL, "Cannot delete the root directory.")

				logging.debug(f"{this.StringId()} is marked for both creation and deletion. Deleting.")
				await this.CommonDelete()
				return

			# Special handling for root directory
			if (this.upath == '' or this.upath == '/'):
				this.cap.rw = this.executor.rootcap
				session = this.executor.GetDatabaseSession()
				query = await session.execute(select(InodeModel).where(InodeModel.id == this.id))
				model = query.scalar()
				model.cap_rw = this.cap.rw
				model.pending_creation = False
				await session.commit()
				await session.close()
				logging.info(f"Root directory (id: {this.id}) created.")
				return

			if (this.executor.strategy.storage == StorageStrategy.MIRROR):
				parent = await this.GetParent()
				if (parent is None or parent.cap.rw is None):
					logging.error(f"Cannot create directory {this.StringId()} without a parent directory.")
					raise IOError(errno.ENOENT, f"Cannot create {this.StringId()} without a parent directory.")
				await this.CommonWrite(parent.cap.rw)

			elif (this.executor.strategy.storage == StorageStrategy.FLAT):
				# nop
				await this.SetState('write', ProcessState.COMPLETE)
			
			else:
				logging.error(f"Unknown storage strategy: {this.executor.strategy.storage}")
				raise IOError(errno.EINVAL, f"Unknown storage strategy: {this.executor.strategy.storage}")


		elif (this.pending.delete):
			if (this.upath == '' or this.upath == '/'):
				logging.error(f"Trying to delete the root directory. Ignoring.")
				raise IOError(errno.EINVAL, "Cannot delete the root directory.")

			await this.SetState('delete', ProcessState.RUNNING)
			
			session = this.executor.GetDatabaseSession()
			query = await session.execute(select(InodeModel).where(InodeModel.id == this.id).options(
				orm.joinedload(InodeModel.children)
			))
			directoryModel = query.scalar()
			for childModel in directoryModel.children:
				directoryModel.children.remove(childModel)
				childModel.pending_deletion = True
				logging.debug(f"Marking child inode {childModel.id} for deletion.")
			await session.commit()
			await session.close()

			for child in this.children:
				await this.executor.delta.SetRedisInodeValue(child, 'last_written', int(time.time()))

			deleteStages = [
				Stage.TAHOE,
				Stage.DATABASE,
				Stage.CACHE,
			]

			if (this.executor.strategy.storage == StorageStrategy.MIRROR):
					# nop
					pass
			elif (this.executor.strategy.storage == StorageStrategy.FLAT):
				deleteStages.remove(Stage.TAHOE)
				try:
					os.rmdir(this.GetPathToCacheOnDisk())
				except Exception as e:
					logging.info(f"Could not delete directory {this.GetPathToCacheOnDisk()}: {e}")
			else:
				logging.error(f"Unknown storage strategy: {this.executor.strategy.storage}")
				raise IOError(errno.EINVAL, f"Unknown storage strategy: {this.executor.strategy.storage}")

			path = await this.GetParentPath()
			await this.CommonDelete(stages=deleteStages, path=path)

	# NOTE: There is no PullDownstream implementation.
	# Directory contents are store in the database, not in tahoe.

	async def AddChild(this, child):
		if child.id not in this.children:
			# NOTE: No change is needed on Tahoe for this right now.
			# In the future, we may add remote topology changes when using multiple parents on a non-flat storage strategy.
			logging.debug(f"Adding child {child.id} to {this.StringId()}")
			this.children.append(child.id)
			await this.Save(True)

	async def RemoveChild(this, child):
		preRemoveLength = len(this.children)
		this.children = [c for c in this.children if c != child.id]
		# TODO: If using a storage strategy other than FLAT, we'll want to adjust the remote topology with this change.
		if (len(this.children) != preRemoveLength):
			logging.debug(f"Removing child {child.id} from {this.StringId()}")
			await this.Accessed(save=False)
			await this.Save(True)


	############################################################################
	# Callable filesystem methods
	############################################################################

	async def GetAttr(this):
		attrs = await super().GetAttr()
		attrs["children_count"] = len(this.children)
		return attrs

	async def List(this):
		await this.Accessed()
		session = this.executor.GetDatabaseSession()
		query = await session.execute(select(InodeModel).where(InodeModel.id.in_(this.children)))
		children = query.scalars().all()
		await session.close()
		return children

	async def Copy(this, dest_upath):
		logging.info(f"Copying {this.StringId()} to {dest_upath}")
		await this.RequireInodeIsNot(File, dest_upath)
		await this.RequireInodeIsNot(Directory, dest_upath) # let's not clobber directories either.
		await this.Accessed(save=False)

		newDir = await Directory.From(this.executor, dest_upath, createIfNotExists=True)
		for (childId) in this.children:
			child = await Inode.FromId(this.executor, childId)
			try:
				await child.Copy(f"{dest_upath}/{child.name}")
			except Exception as e:
				logging.error(f"Error copying child {child.StringId()} to {dest_upath}: {e}")
				continue

		return newDir

	async def Move(this, dest_upath):
		logging.info(f"Moving {this.StringId()} to {dest_upath}")
		await this.RequireInodeIsNot(File, dest_upath)
		await this.RequireInodeIsNot(Directory, dest_upath) # let's not clobber directories either.
		await this.Accessed(save=False)
		await this.CommonMove(dest_upath)

		# When moving a directory, we also need to migrate the upath of all children.
		# This must be done synchronously to allow immediate reads of the directory.

		for (childId) in this.children:
			try:
				child = await Inode.FromId(this.executor, childId)
				await child.Move(f"{dest_upath}/{child.name}")
			except Exception as e:
				logging.error(f"Error moving child {childId} to {dest_upath}: {e}")
				continue

		return this


# RiverFS is a generic file system that adds caching and encryption to a remote file system, specifically TahoeFS.
# All operations should be asynchronous, stateless and scalable, with all state stored in *this.
# NOTE: For thread safety, it is illegal to write to any RiverFS args after it has been started.
# This class is functionally abstract and requires child classes to implement the Function method.
class RiverFS(eons.Executor):
	def __init__(this, name="RiverFS"):
		super().__init__(name)
		this.arg.kw.static.append('rootcap')

		this.arg.kw.optional["tahoe_url"] = "http://127.0.0.1:3456"
		this.arg.kw.optional["cache_dir"] = ".tahoe-cache"
		this.arg.kw.optional["cache_maintenance"] = True  # Whether to run the cache maintenance worker.
		this.arg.kw.optional["cache_size"] = "0"  # Maximum size of the cache. 0 means no limit.
		this.arg.kw.optional["cache_ttl"] = "14400"  # Cache lifetime for filesystem objects (seconds).
		this.arg.kw.optional["net_timeout"] = "30"  # Network timeout (seconds).
		this.arg.kw.optional["backup_interval_max"] = 86400  # Maximum time between backups (seconds).
		this.arg.kw.optional["backup_interval_min"] = 3600  # Minimum time between backups (seconds).
		this.arg.kw.optional["test_compatibility"] = True  # Whether to test system compatibility before starting.
		this.arg.kw.optional["test_integration"] = True  # Whether to test system integration before starting.
		this.arg.kw.optional["test_functionality"] = False  # Whether to test system functionality before starting.
		this.arg.kw.optional["register_classes"] = True  # Whether to register classes included with libtruckeefs
		this.arg.kw.optional["reset_redis"] = True # Whether to reset the Redis semaphore states.
		this.arg.kw.optional["backend_storage_strategy"] = StorageStrategy.FLAT.name  # The storage strategy to use for backend storage.
		this.arg.kw.optional["nuke_tahoe"] = False  # Whether to nuke the Tahoe root directory before starting.
		this.arg.kw.optional["multiprocess_manager"] = None
		this.arg.kw.optional["shared_workers"] = None
		this.arg.kw.optional["is_daemon"] = False  # Whether or not *this has been daemonized.

		this.last_size_check_time = 0

		this.rootId = 1

		this.strategy = eons.util.DotDict()
		this.strategy.storage = None

		# Mapping of Upath to Inode instance.
		this.cache.inodes = {}

		this.main_process = eons.util.DotDict()
		this.main_process.arg = {}

		this.fetch.possibilities.append('main_process')
		this.fetch.use = [
			'main_process',
			'args',
			'this',
			'config',
			'globals',
			'environment'
		]

		# Order matters - it is the order in which tests will be run.
		this.test = eons.util.DotDict()
		this.test.compatibility = [
			"Platform",
			"PythonVersion",
		]
		this.test.integration = [
			"TahoeConnection",
			"Ephemeral",
		]
		this.test.functionality = [
			"InodeModel", # Currently breaks fuse, since root id is no longer 1.
			"FileCreation",
			"FileWrite",
			"FileRead",
			"FileDeletion",
			"DirectoryCreation",
			"SubdirectoryCreation",
			"DirectoryDeletion",
			"DirectoryListing",
			"FileMove",
			"FileCopy",
			"FileLifecycle",
			"InvalidPathFileCreation",
			"OpenNonExistentFile",
			"ReadOnDirectory",
			"WriteOnDirectory",
			"DeleteRootDirectory",
			"MoveFileOverDirectory",
		]

		this.eventLoop = None

		this.process = eons.util.DotDict()
		this.process.prune = None
		this.process.garbage = None
		this.process.retry = None
		this.process.reaper = None
		this.process.backup = None
		this.process.workers = []

	# ValidateArgs is automatically called before Function, per eons.Functor.
	def ValidateArgs(this):
		super().ValidateArgs()

		assert isinstance(this.rootcap, str)

		try:
			this.cache_size = parse_size(str(this.cache_size))
		except ValueError:
			raise eons.MissingArgumentError(f"error: --cache-size {this.cache_size} is not a valid size specifier")
	
		try:
			this.cache_ttl = parse_lifetime(str(this.cache_ttl))
		except ValueError:
			raise eons.MissingArgumentError(f"error: --cache-ttl {this.cache_ttl} is not a valid lifetime")

		try:
			this.net_timeout = float(this.net_timeout)
			if not 0 < this.net_timeout < float('inf'):
				raise ValueError()
		except ValueError:
			raise eons.MissingArgumentError(f"error: --net-timeout {this.net_timeout} is not a valid timeout")

		this.rootcap = this.rootcap.strip()
		this.cache_dir = Path(this.cache_dir).resolve()
		this.cache_dir.mkdir(parents=True, exist_ok=True)

		this.strategy.storage = StorageStrategy[this.backend_storage_strategy.upper()]

		# Prevent the TahoeSyncWorker from trying to stop *this when syncing the root directory.
		this.is_shared = not this.is_daemon


	# Get the arguments for other Executors spwaned by *this.
	def GetWorkerArgs(this):
		ret = this.kwargs.copy()
		ret.update(this.delta.kwargs.copy())
		ret["parent_pid"] = os.getpid()
		ret["is_daemon"] = True
		ret["multiprocess_manager"] = this.multiprocess_manager
		ret['test_compatibility'] = False
		ret['test_integration'] = False
		ret['test_functionality'] = False
		ret['register_classes'] = False
		ret['cache_maintenance'] = False  # Prevent recursion.
		ret['reset_redis'] = False
		return ret


	async def InitializeDatabase(this):
		logging.info(f"Creating database tables.")
		# Base is automatically provided from InodeModel
		async with this.delta.sqlEngine.begin() as db:
			await db.run_sync(Base.metadata.create_all)


	def Function(this):
		if (not this.is_daemon and this.multiprocess_manager is None):
			this.multiprocess_manager = multiprocessing.Manager()
			this.shared_workers = this.multiprocess_manager.list()

		logging.info(f"Starting event loop.")
		if (this.eventLoop is None):
			this.eventLoop = asyncio.new_event_loop()
		this.eventLoopThread = threading.Thread(target=this.RunEventLoop, args=(this.eventLoop,), daemon=True)
		this.eventLoopThread.start()

		if (this.register_classes):
			# Tests are included. We no longer provide any ancillary functors.
			# this.RegisterAllClassesInDirectory(str(Path(__file__).resolve().parent.joinpath("test")))

			if (this.test_compatibility):
				this.TestCompatibility()

		logging.info(f"Connecting to Tahoe.")
		this.source = TahoeConnection()
		this.source(
			this.tahoe_url,
			this.rootcap,
			this.net_timeout
		)
		this.Async(this.source.Open())

		logging.info(f"Connecting to databases.")
		this.delta = RiverDelta()
		this.delta()  # Start the RiverDelta
		if (not this.is_daemon):
			this.Async(this.InitializeDatabase())

		if (this.test_integration):
			this.TestIntegration()

		if (this.reset_redis):
			logging.info(f"Resetting Redis.")
			this.Async(this.delta.redis.flushall())

		logging.info(f"Initializing the root directory")
		# Just need to write to the database, not wait for Tahoe.
		root = this.Async(Directory.From(this, "", createIfNotExists=True, allowSync=(not this.is_daemon)))
		root.cap.rw = this.rootcap
		root.pending.create = False

		if (this.nuke_tahoe and not this.is_daemon):
			# Get user input to confirm tactical strike.
			confirm = input(f"WARNING: This will delete all files and directories under the Tahoe rootcap {this.rootcap}. Type 'yes' to continue: ")
			if (confirm.lower() != "yes"):
				logging.recovery(f"User did not confirm. Aborting.")
				sys.exit(0)

			this.Async(this.source.NukeRoot())

			# Force the user to remove the flag before use.
			sys.exit(0)

		this.SpawnDaemons()

		if (this.register_classes and this.test_functionality):
			this.TestFunctionality()

		logging.info(f"RiverFS is ready.")


	def SpawnDaemon(this, daemon, name, args=None):
		if (args is None):
			args = this.GetWorkerArgs()

		properName = f"{name[0].upper()}{name[1:]}Daemon"

		this.process[name] = multiprocessing.Process(
			target=daemon.Run,
			args=(args,),
			daemon=True,
			name=properName
		)
		this.process[name].start()

		if (this.process[name].is_alive()):
			logging.info(f"{properName} is ready.")
		else:
			logging.error(f"{properName} failed to start.")
			raise TruckeeFSException(f"{properName} failed to start.")

	# Spawn the daemons that will run in the background.
	def SpawnDaemons(this):
		if (this.is_daemon):
			return

		this.SpawnDaemon(GarbageDaemon, "garbage")
		this.SpawnDaemon(RetryDaemon, "retry")
		asyncio.run_coroutine_threadsafe(this.EnsureInodesAreSyncing(), this.eventLoop)

		reaperArgs = this.GetWorkerArgs()
		reaperArgs["shared_workers"] = this.shared_workers
		this.SpawnDaemon(ReaperDaemon, "reaper", reaperArgs)
		asyncio.run_coroutine_threadsafe(this.BuryDeadWorkers(), this.eventLoop)

		if (this.cache_size > 0):
			this.SpawnDaemon(CachePruneDaemon, "prune")

		if (this.backup_interval_max > 0):
			backupArgs = this.GetWorkerArgs()
			backupArgs["shared_workers"] = this.shared_workers
			this.SpawnDaemon(BackupDaemon, "backup", backupArgs)


	def TrackWorkerProcess(this, process, inodeId=None):
		if (not process):
			logging.error(f"Cannot track process: {process}.")
			return

		this.process.workers.append(process)

		logging.debug(f"Tracking process {process.pid} for inode {inodeId}.")

		this.shared_workers.append({
			"pid": process.pid,
			"inode": inodeId,
			# "process": process, # This is not serializable.
			"started": time.time(),
		})

	# The ReaperDaemon will terminate any worker processes that are complete.
	# We just need to join them from here once they're dead.
	async def BuryDeadWorkers(this):
		while (True):
			try:
				remainingWorkers = []
				for process in this.process.workers:
					if (not process.is_alive()):
						logging.debug(f"Joining dead worker process {process.pid}.")
						process.join()
					else:
						remainingWorkers.append(process)
				this.process.workers = remainingWorkers
				logging.debug(f"Remaining worker processes: {len(this.process.workers)}.")
			except Exception as e:
				logging.error(f"Error while burying dead workers: {e}")
			await asyncio.sleep(60)

	# The RetryDaemon will mark any inodes that were unsuccessfully synced as pending_sync.
	# We just need to watch for that and spawn new sync processes for them.
	# NOTE: If a sync process is already running, we will not start a new one (see Inode.py)
	async def EnsureInodesAreSyncing(this):
		while(True):
			try:
				session = this.GetDatabaseSession()
				query = await session.execute(select(InodeModel).where(
					InodeModel.pending_sync == True
				))
				inodes = query.scalars().all()
				await session.close()

				for inode in inodes:
					await asyncio.sleep(1)  # Prevent blocking the event loop too much.
					try:
						if (inode.kind == 'Directory'):
							if (this.strategy.storage == StorageStrategy.FLAT):
								# Directories do not sync in flat storage.
								directory = await Directory.FromId(this, inode.id)
								await directory.Save()
							# TODO: improve support for re-syncing MIRRORed directories.
							continue

						file = await File.From(this, inode.upath)
						await file.InitiateSync("UP")

					except Exception as e:
						logging.error(f"{this.name}: Failed to initiate sync for {inode.upath}: {e}")
			except Exception as e:
				logging.error(f"{this.name}: Error while ensuring inodes are syncing: {e}")
			await asyncio.sleep(3600)  # Wait before checking again.


	# Async thread-safe means of caching a new Inode.
	async def CacheInode(this, inode):
		logging.debug(f"Caching {inode.StringId()}.")
		this.cache.inodes[inode.upath] = inode
		# If running RiverFS in a multi-server deployment, the inode may have been initialized on another server.
		if (not await inode.AreProcessStatesInitialized()):
			await inode.InitializeProcessStates()
			await inode.InitializeEphemerals()

	async def PurgeCachedInode(this, inode):
		if (inode.upath in this.cache.inodes):
			logging.debug(f"Purging {inode.StringId()} from cache.")
			del this.cache.inodes[inode.upath]

	def GetCachedInodeByUpath(this, upath):
		return this.cache.inodes.get(upath)


	def GetDatabaseSession(this):
		session = this.delta.sql()

		# Get the pool from the engine
		pool = this.delta.sqlEngine.pool

		# Log stats
		# logging.debug("Session created: %s", session)
		# logging.debug("Pool status — Checked out: %d / Pool size: %d / Overflow: %d / Connections in overflow: %d",
		# 	pool.checkedout(),
		# 	pool.size(),
		# 	pool._max_overflow,
		# 	pool.overflow()
		# )
		
		return session

	def GetSourceConnection(this):
		return this.source

	def GetUpathRootId(this):
		return this.rootId


	def Test(this, tests):
		for test in tests:
			testFunctor = eval(f"Test{test}()")
			# It is fatal if we try to execute a test that we can't find.
			testFunctor(executor=this)
			time.sleep(3)

	def TestCompatibility(this):
		this.Test(this.test.compatibility)

	def TestIntegration(this):
		this.Test(this.test.integration)

	def TestFunctionality(this):
		this.Test(this.test.functionality)


	def RunEventLoop(this, eventLoop):
		asyncio.set_event_loop(eventLoop)
		eventLoop.run_forever()


	# This is a thread-safe way to run a coroutine in the event loop.
	# Use this to run async functions from synchronous (i.e. non-async) code.
	# coro is the fully defined coroutine to run (NOTE that coroutines are returned by async invokations, they are not typical function pointers: they have all arguments supplied)
	# timeout is the maximum time to wait for the coroutine to finish.
	# Returns the result of the coroutine.
	# NOTE: This will block the calling thread until the coroutine is finished.
	def Async(this, coro, timeout=120):
		starttime = time.time()
		future = asyncio.run_coroutine_threadsafe(coro, this.eventLoop)
		while (not future.done()):
			time.sleep(0.01)
			if (timeout and time.time() - starttime > timeout):
				logging.error(f"Timeout waiting for coroutine to finish: {coro}")
				return None
		return future.result()


	def Stop(this):
		logging.info(f"Stopping RiverFS.")

		logging.debug(f"Stopping Tahoe.")
		this.Async(this.source.Close())

		logging.debug(f"Stopping RiverDelta.")
		this.Async(this.delta.Close())

		for daemon in ['garbage', 'retry', 'prune', 'reaper']:
			process = getattr(this.process, daemon)
			if (process is not None):
				logging.info(f"Stopping {daemon} daemon...")
				process.terminate()
				process.join()

		this.eventLoop.stop()
		this.eventLoopThread.join()

	# For passing arguments to subprocesses.
	def fetch_location_main_process(this, varName, default, fetchFrom, attempted):
		try:
			return this.main_process.arg[varName], True
		except KeyError:
			return default, False

class UniversalPath:
	def __init__(this, path=""):
		if (isinstance(path, UniversalPath)):
			this.upath = path.upath
		elif (isinstance(path, str)):
			this.FromPath(path)

	def __str__(this):
		return this.upath

	def FromPath(this, path):
		assert isinstance(path, str)
		try:
			path = os.path.normpath(path)
			this.upath = path.replace(os.sep, "/").lstrip('/')
		except UnicodeError:
			raise IOError(errno.ENOENT, "file does not exist")

	def AsPath(this):
		return this.upath.replace(os.sep, "/")

	def GetParent(this):
		return UniversalPath(os.path.dirname(this.upath))

	# Compatibility for str method.
	def encode(this, encoding='utf-8'):
		return this.upath.encode(encoding)
Base = orm.declarative_base()


# Association table for parent-child inode relationships
inode_association = sql.Table(
    'inode_association',
    Base.metadata,
    sql.Column(
        'parent_id',
        sql.Integer,
        sql.ForeignKey('fs.id', ondelete='CASCADE'),
        primary_key=True
    ),
    sql.Column(
        'child_id',
        sql.Integer,
        sql.ForeignKey('fs.id', ondelete='CASCADE'),
        primary_key=True
    )
)

# InodeModel class to store metadata for files and directories
class InodeModel(Base):
	__tablename__ = 'fs'
	__table_args__ = {'mysql_charset': 'utf8'}

	# Lookup info
	id = sql.Column(sql.Integer, primary_key=True)
	upath = sql.Column(sql.String(1024), nullable=False, unique=True)  # Set max length
	name = sql.Column(sql.String(255), nullable=False)  # Set max length
	kind = sql.Column(sql.String(32), nullable=False)  # Set max length

	# Filesystem data
	meta = sql.Column(sql.JSON)  # JSON is supported in MySQL 5.7+ and MariaDB 10.2+
	last_accessed = sql.Column(sql.Integer, default=0)
	
	# Many-to-many relationship for parent-child inodes
	parents = orm.relationship(
		'InodeModel',
		secondary=inode_association,
		primaryjoin=id == inode_association.c.child_id,
		secondaryjoin=id == inode_association.c.parent_id,
		backref=orm.backref('children', lazy='selectin'),
		lazy='selectin'
	)

	data = sql.Column(sql.Text)  # Use Text for large strings

	# Cache info
	cache_strategy = sql.Column(sql.String(32), default=CacheStrategy.ONDEMAND.name)
	pending_sync = sql.Column(sql.Boolean, default=False)
	pending_creation = sql.Column(sql.Boolean, default=False)
	pending_deletion = sql.Column(sql.Boolean, default=False)

	# Tahoe info
	cap_ro = sql.Column(sql.String(255))  # Read-only URI for Tahoe
	cap_rw = sql.Column(sql.String(255))  # Read-write URI for Tahoe

	def __repr__(self):
		return f"<{self.name} ({self.id}) @ {self.upath}>"

	def __init__(self):
		pass


class BackupModel(Base):
    __tablename__ = "backup_metadata"
    __table_args__ = {'mysql_charset': 'utf8'}

    id = sql.Column(sql.Integer, primary_key=True)
    stardate = sql.Column(sql.String(64), nullable=False, unique=True)
    cap = sql.Column(sql.Text, nullable=False)  # Tahoe cap
    size = sql.Column(sql.Integer, nullable=False)
    hash = sql.Column(sql.String(64), nullable=False)  # sha256 of encrypted file
    created_at = sql.Column(sql.Integer, nullable=False)  # UNIX epoch

    def __repr__(self):
        return f"<Backup {self.stardate}: {self.cap[:20]}...>"


class TahoeSyncWorker(eons.Functor):

	# Common tasks for SyncWorkers.
	# If any of these fail, the system (e.g. database) will be in a bad state.
	@staticmethod
	def SyncWorkerCommon(kwargs):

		# Get our initial data.
		try:
			inodeId = kwargs.pop('inode_id')
		except Exception as e:
			logging.error(f"Error syncing: {e}")
			# Can't clear database. This is also bad.
			raise e

		# Initialize the Executor.
		if ('executor' in kwargs):
			logging.debug(f"Running Sync process for Inode {inodeId} synchronously on PID {os.getpid()}.")
			executor = kwargs.pop('executor')
			executor.is_shared = True
		else:
			try:
				executor = RiverFS(f"RiverFS Sync for {inodeId}")
				for key, value in kwargs.items():
					executor.main_process.arg[key] = value
				executor()
				executor.is_shared = False
			except Exception as e:
				logging.error(f"Error syncing {inodeId}: {e}")
				# Can't clear database. This is bad.
				TahoeSyncWorker.Stop(executor, 9)

		# Startup loop.
		# Claims sync host and pid to ensure that only one sync process is running per inode at a time.
		# 10s timeout.
		for i in range(10):
			syncPid = executor.Async(executor.delta.GetRedisInodeValue(inodeId, 'sync_pid'))
			syncHost = executor.Async(executor.delta.GetRedisInodeValue(inodeId, 'sync_host'))
			if ((syncPid is None or not len(syncPid) or (syncHost is None or not len(syncHost)))):
				# No sync process is running. Let's claim it!
				logging.debug(f"Starting sync process for {inodeId} on PID {os.getpid()}.")
				executor.Async(executor.delta.SetRedisInodeValue(inodeId, 'sync_pid', os.getpid(), syncPid))
				executor.Async(executor.delta.SetRedisInodeValue(inodeId,'sync_host', socket.gethostname(), syncHost))

				if (i == 9):
					logging.error(f"Sync process for {inodeId} failed to start after 10 seconds.")
					executor.Async(TahoeSyncWorker.CompleteSync(executor, inode, False))
					TahoeSyncWorker.Stop(executor, 1)
				else:
					executor.Async(asyncio.sleep(1))
					continue

			elif (int(syncPid) != os.getpid() or syncHost != socket.gethostname()):
				logging.debug(f"Sync process already running for {inodeId} ({syncPid} is running on {syncHost}, but I am {os.getpid()} on {socket.gethostname()}).")
				TahoeSyncWorker.Stop(executor, 0)
			else:
				break

		return executor, inodeId


	# Sync an Inode downstream from the source (i.e. Tahoe).
	# This is a high(ish) priority background task.
	# It should be spawned from multiprocessing.Process.
	# Most logic is implemented in the Inode subclass.
	# To modify the sync behavior, override the following methods in your Inode subclass:
	# - BeforePullDownstream
	# - PullDownstream
	# - AfterPullDownstream
	#
	# NOTE: THIS RUNS ON DEMAND! It DOES NOT regularly check for changes upstream.
	# This means you cannot use Tahoe to synchronize data across regions / geo-distributed servers.
	#
	@staticmethod
	def DownstreamSyncWorker(kwargs):
		executor, inodeId = TahoeSyncWorker.SyncWorkerCommon(kwargs)
		inode = executor.Async(TahoeSyncWorker.GetInode(executor, inodeId))

		try:
			executor.Async(TahoeSyncWorker.PullDownstreamFromSource(executor, inode))
		except Exception as e:
			logging.error(f"Error syncing {inodeId}: {e}")
			eons.util.LogStack()
			executor.Async(TahoeSyncWorker.CompleteSync(executor, inode, False))
			TahoeSyncWorker.Stop(executor, 1)

		executor.Async(TahoeSyncWorker.CompleteSync(executor, inode))
		TahoeSyncWorker.Stop(executor, 0)


	# Sync an Inode upstream toward the source (i.e. Tahoe).
	# This is a background task that runs with the lowest possible priority.
	# It should be spawned from multiprocessing.Process.
	# See Inode.Save for an example.
	#
	# To modify the sync behavior, override the following methods in your Inode subclass:
	# - Freeze
	# - BeforePushUpstream
	# - PushUpstream
	# - AfterPushUpstream
	@staticmethod
	def UpstreamSyncWorker(kwargs):
		# Set the process priority to low (nice level 19)
		# In Unix-like systems, the nice level ranges from -20 (highest priority) to 19 (lowest priority). 
		# Setting the nice level to 19 ensures that the sync process runs with the lowest possible priority, which is ideal for background tasks that shouldn't interfere with the performance of higher-priority tasks, like user interactions or other critical processes.
		# NOTE: This may only work on Linux.
		os.nice(19)

		executor, inodeId = TahoeSyncWorker.SyncWorkerCommon(kwargs)
		inode = executor.Async(TahoeSyncWorker.GetInode(executor, inodeId))

		try:
			frozen_data = kwargs.pop('frozen_data')
		except Exception as e:
			try: 
				frozen_data = executor.Async(inode.Freeze())
			except Exception as e:
				logging.error(f"Error syncing {inodeId}: {e}")
				eons.util.LogStack()
				executor.Async(TahoeSyncWorker.CompleteSync(executor, inode, False))
				TahoeSyncWorker.Stop(executor, 1)

		deleteState = ProcessState.IDLE

		# Sync loop.
		while (True):
			possibleDelete = deleteState in [ProcessState.PENDING, ProcessState.RUNNING, ProcessState.COMPLETE]
			try:
				inode = executor.Async(TahoeSyncWorker.GetInode(executor, inodeId, possibleDelete=possibleDelete))
			except Exception as e:
				if (possibleDelete):
					logging.debug(f"Succesfully deleted Inode {inodeId}. Exiting.")
					# No CompleteSync here, as the inode is now invalid.

					# hack the sync state in case anyone is watching.
					executor.Async(executor.delta.SetState(inodeId, 'sync', ProcessState.COMPLETE))
					TahoeSyncWorker.Stop(executor, 0)

				else:
					logging.error(f"Error syncing {inodeId}: {e}")
					eons.util.LogStack()
					executor.Async(TahoeSyncWorker.CompleteSync(executor, inode, False))
					TahoeSyncWorker.Stop(executor, 1)

			deleteState = executor.Async(inode.GetState('delete'))
			if (deleteState == ProcessState.IDLE):
				# Wait for any open writes to finish; iff that write is not a delete.
				executor.Async(inode.WaitForStateBesides('write', ProcessState.RUNNING))
			else:
				executor.Async(inode.SetState('delete', ProcessState.RUNNING))
			executor.Async(inode.SetState('sync', ProcessState.RUNNING))

			try:
				# Check if the data changed while we were syncing the object.
				# Doing this here (rather than spawning a new process) helps conserve resources and should make syncing faster overall.
				if (frozen_data is None):
					syncAgain = executor.Async(inode.GetEphemeral('sync_again', coerceType=bool))
					if (not syncAgain):
						logging.debug(f"Inode {inode.name} (id: {inodeId}) has synchronized. Exiting.")
						break

					frozen_data = executor.Async(inode.Freeze())

				# Refresh the Ephemeral values.
				executor.Async(inode.SetEphemeral('sync_again', False))

				# These values will be None if the expected value (2nd arg) does not match the first.
				# (or they were set to None)
				stillRunningSyncOnPid = executor.Async(inode.SetEphemeral('sync_pid', os.getpid(), os.getpid()))
				stillRunningSyncOnHost = executor.Async(inode.SetEphemeral('sync_host', socket.gethostname(), socket.gethostname()))

				if (stillRunningSyncOnPid is None or stillRunningSyncOnHost is None):
					logging.error(f"Sync process for {inodeId} ({inode.name}) was interrupted.")
					raise Exception(f"Sync process for {inodeId} ({inode.name}) was interrupted.")

				# Perform the Sync.
				if (inode.frozen is None or not len(inode.frozen)):
					inode.frozen = frozen_data
				executor.Async(TahoeSyncWorker.PushUpstreamToSource(executor, inode))
				frozen_data = None

			except Exception as e:
				logging.error(f"Error syncing {inodeId}: {e}")
				eons.util.LogStack()
				executor.Async(TahoeSyncWorker.CompleteSync(executor, inode, False))
				TahoeSyncWorker.Stop(executor, 1)

			# Flush cache at the end of each loop so we make sure to grab the latest data.
			executor.Async(executor.PurgeCachedInode(inode))

		# Cleanup			
		executor.Async(TahoeSyncWorker.CompleteSync(executor, inode))
		TahoeSyncWorker.Stop(executor, 0)


	# Get the Inode we'll be syncing.
	@staticmethod
	async def GetInode(executor, inodeId, possibleDelete=False):
		try:
			# NOTE: This double lookup is a bit inefficient right now.
			# Currently the Inode and children use upath as a unique "name", but here we use the Inode's numeric id.
			# However, since this runs in the background and is relatively light, we'll leave it alone.
			db = executor.GetDatabaseSession()
			query = await db.execute(select(InodeModel).where(InodeModel.id == inodeId))
			upath = query.scalar().upath
			# NOTE: allowSync needs to be false to prevent "daemonic processes are not allowed to have children" errors.
			inode = await Inode.From(executor, upath, createIfNotExists=False, allowSync=False)
			logging.debug(f"Inode {inode.name} (id: {inodeId}) ready to sync.")
			await db.close()

		except Exception as e:
			if (not possibleDelete):
				logging.error(f"Could not get Inode {inodeId} to sync: {e}")
			raise e
		return inode


	# Perform the upstream Sync.
	# Update some data in the source (i.e. Tahoe).
	@staticmethod
	async def PushUpstreamToSource(executor, inode):
		try:
			await inode.BeforePushUpstream()
			await inode.PushUpstream()
			await inode.AfterPushUpstream()
			logging.debug(f"Inode {inode.name} (id: {inode.id}) pushed upstream.")
		except Exception as e:
			logging.error(f"Error syncing {inode.id}: {e}")
			eons.util.LogStack()
			raise e

	# Perform the downstream Sync.
	# Update some data in the local cache.
	@staticmethod
	async def PullDownstreamFromSource(executor, inode):
		try:
			await inode.BeforePullDownstream()
			await inode.PullDownstream()
			await inode.AfterPullDownstream()
			await inode.Save(mutated=False) # We just pulled, so obviously not mutated compared to the remote.
			logging.debug(f"Inode {inode.name} (id: {inode.id}) pulled downstream and saved.")
		except Exception as e:
			logging.error(f"Error syncing {inode.id}: {e}")
			eons.util.LogStack()
			raise e


	# Release database locks
	@staticmethod
	async def CompleteSync(executor, inode, successful=True):
		try:
			if (successful):
				await inode.SetState('sync', ProcessState.COMPLETE)
			else:
				await inode.SetState('sync', ProcessState.ERROR)
			await inode.SetEphemeral('sync_pid', "", os.getpid())
			await inode.SetEphemeral('sync_host', "", socket.gethostname())
			success = "successful" if successful else "unsuccessful"
			logging.info(f"Inode {inode.upath} (id: {inode.id}) sync {success}.")
		except Exception as e:
			logging.error(f"Error completing sync: {e}")
			eons.util.LogStack()

	@staticmethod
	def Stop(executor, exitCode=0):
		try:
			if (not executor.is_shared):
				executor.Stop()
		finally:
			sys.exit(exitCode)

# ./lib/daemon/BackupDaemon.py

class BackupDaemon(Daemon):
	def __init__(this, name="Backup Daemon"):
		super().__init__(name)

		this.arg.kw.static.append("sql_backup_user")
		this.arg.kw.static.append("sql_backup_pass")
		this.arg.kw.optional["retention_max"] = 30  # Max number of backups to keep

		this.lastBackupTime = 0


	def BeforeFunction(this):
		this.interval_min = int(this.executor.backup_interval_min)
		this.interval_max = int(this.executor.backup_interval_max)


	async def Worker(this):
		now = time.time()
		timeSinceLast = now - this.lastBackupTime
		if (timeSinceLast < this.interval_min):
			logging.debug(f"{this.name}: Backup interval not met. Waiting {this.interval_min - timeSinceLast:.2f} seconds.")
			return

		reason = None
		if (timeSinceLast >= this.interval_max):
			reason = "interval_max"
		elif (await this.IsNowAGoodTimeToBackup()):
			reason = "good_time"

		if (reason):
			logging.debug(f"{this.name}: Backing up because '{reason}'.")
			try:
				await this.PerformBackup()
				this.lastBackupTime = time.time()
			except Exception as e:
				logging.error(f"Backup failed: {e}")


	async def IsNowAGoodTimeToBackup(this):
		return len(list(this.executor.shared_workers)) == 0


	async def PerformBackup(this):
		logging.info("Performing backup...")

		delta = this.executor.delta
		tahoe = this.executor.source
		rootcap = this.executor.rootcap
		stardate = EOT.GetStardate()  # format: 2025.2654737542

		backup_dir = tempfile.mkdtemp()
		try:
			# Dump MySQL DB to file
			dump_path = os.path.join(backup_dir, "backup.sql")
			mysqldumpArgs = [
				"--protocol=TCP",
				"--skip-lock-tables",
				"--single-transaction",
				f"-h{this.executor.delta.sql_host.replace('localhost', '127.0.0.1')}",
				f"-P{this.executor.delta.sql_port}",
				f"-u{this.sql_backup_user}",
				f"-p{this.sql_backup_pass}",
				this.executor.delta.sql_db,
				f"-r{dump_path}",
			]
			this.RunCommand(f"mysqldump {' '.join(mysqldumpArgs)}")

			# Compress
			compressed_path = f"{dump_path}.gz"
			with open(dump_path, "rb") as f_in, gzip.open(compressed_path, "wb") as f_out:
				shutil.copyfileobj(f_in, f_out)

			# Encrypt
			with open(compressed_path, "rb") as f:
				data = f.read()

			key = base64.urlsafe_b64encode(hashlib.sha256(rootcap.encode()).digest())
			encrypted = Fernet(key).encrypt(data)

			enc_path = os.path.join(backup_dir, f"{stardate}.enc")
			with open(enc_path, "wb") as f:
				f.write(encrypted)

			# Upload to Tahoe under /backup/<stardate>.enc
			cap = await tahoe.Put(f"/backup/{stardate}.enc", enc_path)

			# Log metadata (or insert into DB later)
			logging.info(f"Backup complete: {stardate} => {cap} (size: {len(encrypted)} bytes)")

			async with this.executor.GetDatabaseSession() as session:
				meta = BackupModel(
					stardate=stardate,
					cap=cap,
					size=len(encrypted),
					hash=hashlib.sha256(encrypted).hexdigest(),
					created_at=int(time.time())
				)
				session.add(meta)

				await session.commit()
				try:
					await this.EnforceRetention(session)
				except Exception as e:
					logging.error(f"Failed to enforce retention policy: {e}")

				await session.close()

		finally:
			shutil.rmtree(backup_dir)

	# Enforce backup retention policy
	async def EnforceRetention(this, session):
		result = await session.execute(select(BackupModel).order_by(BackupModel.created_at.desc()))
		backups = result.scalars().all()
		if (len(backups) > this.retention_max):
			tahoe = this.executor.GetSourceConnection()

			for old in backups[this.retention_max:]:
				logging.info(f"Deleting old backup: {old.stardate} => {old.cap}")
				try:
					deleteResponse = await tahoe.Delete(old.cap, iscap=True)
				except aiohttp.ClientResponseError as e:
					if (e.status not in [404, 410]):
						logging.error(f"Error deleting backup {old.stardate} from Tahoe: {e}")
					continue

				await session.delete(old)

			logging.debug(f"Enforced backup retention: kept {this.retention_max}, deleted {len(backups[this.retention_max:])}")
		await session.commit()

class RetryDaemon(Daemon):
	def __init__(this, name="Retry Daemon"):
		super().__init__(name)
		this.arg.kw.optional["sleep"] = 3600

	async def Worker(this):
		try:
			session = this.executor.GetDatabaseSession()
			# Select inodes that:
			# - Have a non-null data field (i.e. cached file exists),
			# - Haven't been accessed recently (last_accessed < current_time - ttl),
			# - And are not pending any operations.
			query = await session.execute(select(InodeModel).where(
				InodeModel.kind == 'File',
				InodeModel.data.isnot(None),
				InodeModel.cap_rw.is_(None),
				InodeModel.pending_sync == False,
				InodeModel.pending_creation == False,
				InodeModel.pending_deletion == False
			))
			inodes = query.scalars().all()

			for inode in inodes:
				logging.info(f"{this.name}: Scheduling retry sync for file {inode.upath}")
				inode.pending_sync = True
			await session.commit()
			await session.close()
		except Exception as e:
			logging.error(f"{this.name}: Error querying database: {e}")
			try:
				await session.close()
			except:
				pass
			return


