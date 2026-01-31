"""
Build script for creating standalone .exe
Run with: python build_exe.py
"""
import PyInstaller.__main__
import shutil
from pathlib import Path

def build():
    """Build standalone executable"""
    
    print("="*60)
    print("  CyberDrive - Build Executable")
    print("="*60)
    print()
    
    # Clean previous builds
    print("Cleaning previous builds...")
    dist_path = Path("dist")
    build_path = Path("build")
    
    if dist_path.exists():
        shutil.rmtree(dist_path)
    if build_path.exists():
        shutil.rmtree(build_path)
    
    print("Building executable with PyInstaller...")
    print()
    
    # PyInstaller arguments
    args = [
        'main_ui.py',                    # Entry point
        '--name=CyberDrive',             # Executable name
        '--onefile',                     # Single file
        '--windowed',                    # No console window
        '--add-data=config;config',      # Include config folder
        '--add-data=ui/resources;ui/resources',  # Include resources
        '--hidden-import=PyQt6',
        '--hidden-import=serial',
        '--hidden-import=yaml',
        '--hidden-import=colorama',
        '--collect-all=PyQt6',
        '--noconfirm',                   # Overwrite without asking
    ]
    
    # Optional: Add icon if you have one
    # icon_path = Path("resources/icon.ico")
    # if icon_path.exists():
    #     args.append(f'--icon={icon_path}')
    
    PyInstaller.__main__.run(args)
    
    print()
    print("="*60)
    print("  Build Complete!")
    print("="*60)
    print()
    print(f"Executable location: {dist_path / 'CyberDrive.exe'}")
    print()
    print("You can now run CyberDrive.exe from the dist/ folder")
    print()

if __name__ == "__main__":
    try:
        build()
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        import traceback
        traceback.print_exc()