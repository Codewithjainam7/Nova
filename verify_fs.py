import asyncio
import os
import time
from backend.desktop.core import DesktopEngine
from backend.desktop.schema import DesktopAction, DesktopActionType, DesktopPermissionLevel

async def run_verification():
    print("Starting Desktop Filesystem Verification...")
    engine = DesktopEngine()
    results = []
    
    start_time = time.time()
    errors = []

    def record(name, condition, err=None):
        status = "PASS" if condition else "FAIL"
        results.append(f"{name}: {status}")
        if err:
            errors.append(f"{name} Error: {err}")
        print(f"[{status}] {name}")

    test_dir = os.path.join(os.getcwd(), "Desktop", "TestFolder")
    test_file = os.path.join(test_dir, "hello.txt")
    rename_file = os.path.join(test_dir, "renamed.txt")
    copy_file = os.path.join(test_dir, "copy.txt")
    move_dir = os.path.join(os.getcwd(), "Desktop", "MoveFolder")
    move_file = os.path.join(move_dir, "copy.txt")

    # Cleanup before test
    import shutil
    if os.path.exists(os.path.join(os.getcwd(), "Desktop")):
        shutil.rmtree(os.path.join(os.getcwd(), "Desktop"), ignore_errors=True)

    try:
        # Create directory
        await engine.perform_action(DesktopAction(
            action_type=DesktopActionType.FS_CREATE_DIRECTORY,
            payload={"path": test_dir}
        ))
        record("Create directory", os.path.isdir(test_dir))

        # Create file
        await engine.perform_action(DesktopAction(
            action_type=DesktopActionType.FS_CREATE_FILE,
            payload={"path": test_file}
        ))
        record("Create file", os.path.isfile(test_file))

        # Write file
        await engine.perform_action(DesktopAction(
            action_type=DesktopActionType.FS_WRITE,
            payload={"path": test_file, "text": "Hello NOVA"}
        ))
        with open(test_file, 'r') as f:
            content = f.read()
        record("Write file", content == "Hello NOVA")

        # Read file
        res = await engine.manager.dispatcher.dispatch(DesktopAction(
            action_type=DesktopActionType.FS_READ,
            payload={"path": test_file}
        ))
        record("Read file", res == "Hello NOVA")

        # Rename file
        await engine.perform_action(DesktopAction(
            action_type=DesktopActionType.FS_RENAME,
            payload={"path": test_file, "new_name": rename_file}
        ))
        record("Rename file", os.path.isfile(rename_file) and not os.path.isfile(test_file))

        # Copy file
        await engine.perform_action(DesktopAction(
            action_type=DesktopActionType.FS_COPY,
            payload={"path": rename_file, "destination": copy_file}
        ))
        record("Copy file", os.path.isfile(rename_file) and os.path.isfile(copy_file))

        # Move file
        os.makedirs(move_dir, exist_ok=True)
        await engine.perform_action(DesktopAction(
            action_type=DesktopActionType.FS_MOVE,
            payload={"path": copy_file, "destination": move_file}
        ))
        record("Move file", os.path.isfile(move_file) and not os.path.isfile(copy_file))

        # Delete file
        await engine.perform_action(DesktopAction(
            action_type=DesktopActionType.FS_DELETE,
            payload={"path": rename_file}
        ))
        record("Delete file", not os.path.isfile(rename_file))

        # Delete directory
        await engine.perform_action(DesktopAction(
            action_type=DesktopActionType.FS_DELETE,
            payload={"path": test_dir}
        ))
        record("Delete directory", not os.path.isdir(test_dir))

        # Permission enforcement (Read-only should fail write)
        ro_engine = DesktopEngine(permission_level=DesktopPermissionLevel.READ_ONLY)
        try:
            await ro_engine.perform_action(DesktopAction(
                action_type=DesktopActionType.FS_CREATE_DIRECTORY,
                payload={"path": "dummy"}
            ))
            record("Permission enforcement", False, "Read-only engine allowed FS_CREATE_DIRECTORY")
        except PermissionError:
            record("Permission enforcement", True)

    except Exception as e:
        import traceback
        traceback.print_exc()
        errors.append(str(e))

    execution_time = time.time() - start_time
    
    with open("docs/DESKTOP_FILESYSTEM_VERIFICATION.md", "w", encoding="utf-8") as f:
        f.write("# Desktop Filesystem Verification\n\n")
        f.write(f"**Execution Time**: {execution_time:.2f} seconds\n\n")
        f.write("## Tests\n")
        for res in results:
            f.write(f"- {res}\n")
        f.write("\n## Errors\n")
        if not errors:
            f.write("None\n")
        else:
            for err in errors:
                f.write(f"- {err}\n")

if __name__ == "__main__":
    asyncio.run(run_verification())