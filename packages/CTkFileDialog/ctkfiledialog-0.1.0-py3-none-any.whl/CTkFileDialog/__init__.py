#!/usr/bin/env python
from io import *
from pathlib import Path
from .Dialog import *

def askopenfilename(filetypes: Optional[List[str]] = None,
                    hidden: bool = False, 
                    preview_img: bool = False,
                    autocomplete: bool = False,
                    video_preview: bool = False,
                    initial_dir: str = str(Path.cwd()),
                    tool_tip: bool = False,
                    ) -> str | None:
    """
    Displays a file dialog for selecting a single file and returns the file path.
    
    This function creates a modal dialog that allows the user to navigate the filesystem
    and select a single file. Various display options can be configured.

    Args:
        filetypes: List of file type filters (e.g., ['.py', 'sh', '.md'])
        hidden: If True, shows hidden files/directories
        preview_img: Enables live preview of image files
        autocomplete: Enables path autocompletion in the input field
        video_preview: Enables video preview capability (if implemented)
        initial_dir: Initial directory to display (defaults to current working directory)
        tool_tip: Enables tooltips with file information on hover

    Returns:
        str: Absolute path to the selected file, or None if canceled

    Example:
        >>> file_path = askopenfilename(
        ...     filetypes=['.py', '.md', '.jpg', '.mp4', '.mvk'],
        ...     preview_img=True
        ... )
        >>> print(f"Selected: {file_path}")
    """

    app = DrawApp(filetypes=filetypes,
                  current_path=initial_dir,
                  hidden=hidden,
                  preview_img=preview_img,
                  method='askopenfilename', 
                  autocomplete=autocomplete, 
                  video_preview=video_preview, 
                  tool_tip=tool_tip)

    app.app.wait_window()
    return app.selected_file if app.selected_file else None

def askdirectory(filetypes: Optional[List[str]] = None,
                 hidden: bool = False, 
                 autocomplete: bool = False,
                 initial_dir: str = str(Path.cwd()),
                 tool_tip: bool = False,
                 ) -> str | None:
    """
    Displays a directory selection dialog and returns the selected path.

    This dialog allows users to navigate and select a single directory.
    Similar to askopenfilename but optimized for directory selection.

    Args:
        filetypes: Optional file type filters (affects display in some implementations)
        hidden: Enables showing hidden directories when True
        autocomplete: Enables path autocompletion feature
        initial_dir: Starting directory (defaults to current working directory)
        tool_tip: Enables directory information tooltips

    Returns:
        str: Path to the selected directory, or None if canceled

    Example:
        >>> dir_path = askdirectory(
        ...     initial_dir="~/Documents",
        ...     hidden=True
        ... )
        >>> if dir_path:
        ...     print(f"Chose directory: {dir_path}")
    """
    app = DrawApp(filetypes=filetypes,
                  current_path=initial_dir,
                  hidden=hidden,
                  method='askdirectory',
                  autocomplete=autocomplete,
                  tool_tip=tool_tip)

    app.app.wait_window()
    return app.selected_file if app.selected_file else None

def askopenfilenames(filetypes: Optional[List[str]] = None,
                     hidden: bool = False, 
                     preview_img: bool = False,
                     autocomplete: bool = False,
                     video_preview: bool = False,
                     initial_dir: str = str(Path.cwd()),
                     tool_tip: bool = False,
                     ) -> tuple[str] | None:
    """
    Displays a file dialog for multiple file selection.

    Allows user to select multiple files through Ctrl+Click.
    Returns a tuple of selected file paths.

    Args:
        filetypes: File type filters (e.g., ['jpg', '.png', '.py'])
        hidden: Shows hidden files when enabled
        preview_img: Enables image preview functionality
        autocomplete: Activates path autocompletion
        video_preview: Enables video file previews
        initial_dir: Initial directory to display
        tool_tip: Shows file metadata tooltips

    Returns:
        tuple[str]: Tuple of selected file paths, or None if canceled

    Example:
        >>> selected_files = askopenfilenames(
        ...     filetypes=[("Images", "*.jpg *.png")],
        ...     preview_img=True
        ... )
        >>> for file in selected_files:
        ...     process_file(file)
    """
    app = DrawApp(filetypes=filetypes,
                  current_path=initial_dir,
                  hidden=hidden,
                  preview_img=preview_img,
                  method='askopenfilenames',
                  autocomplete=autocomplete,
                  video_preview=video_preview, 
                  tool_tip=tool_tip)

    app.app.wait_window()
    return tuple(app.selected_objects) if app.selected_objects else None

def asksaveasfilename(filetypes: Optional[List[str]] = None,
                      hidden: bool = False, 
                      preview_img: bool = False,
                      autocomplete: bool = False,
                      video_preview: bool = False,
                      initial_dir: str = str(Path.cwd()),
                      tool_tip: bool = False, 
                      ) -> str | None:
    """
    Displays a save file dialog and returns the selected path.

    This dialog allows users to specify a new file location for saving.
    Note: Does not actually create or save the file.

    Args:
        filetypes: Suggested file extensions (e.g., ['.pdf', '.jpg'])
        hidden: Shows hidden items when enabled
        preview_img: Enables preview of existing images
        autocomplete: Activates path suggestion
        video_preview: Enables video previews
        initial_dir: Default starting directory
        tool_tip: Shows file information tooltips

    Returns:
        str: Path where file should be saved, or None if canceled

    Example:
        >>> save_path = asksaveasfilename(
        ...     filetypes=['.py', '.png', '.sh', '.bat'],
        ...     initial_dir="~/Documents"
        ... )
        >>> if save_path:
        ...     with open(save_path, 'w') as f:
        ...         f.write("File content")
    """
    app = DrawApp(filetypes=filetypes,
                  current_path=initial_dir,
                  hidden=hidden,
                  preview_img=preview_img,
                  method='asksaveasfilename', 
                  autocomplete=autocomplete, 
                  video_preview=video_preview, 
                  tool_tip=tool_tip)

    app.app.wait_window()
    return app.selected_file if app.selected_file else None

def asksaveasfile(mode: Literal['r', 'rb', 'r+', 'rb+', 'r+b','w', 'wb', 'w+', 'wb+','a', 'ab', 'a+', 'ab+','x', 'xb'] = 'w',
                  filetypes: Optional[List[str]] = None,
                  hidden: bool = False, 
                  preview_img: bool = False,
                  autocomplete: bool = False,
                  video_preview: bool = False,
                  initial_dir: str = str(Path.cwd()),
                  tool_tip: bool = False,
                  **kwargs,
                  ):
    """
    Displays a save dialog and returns an open file object.

    Combines asksaveasfilename with automatic file opening.
    The returned file object is already opened in the specified mode.

    Args:
        mode: File opening mode (defaults to 'w' for write)
        filetypes: Suggested file extensions
        hidden: Shows hidden files when True
        preview_img: Enables image preview
        autocomplete: Activates path completion
        video_preview: Enables video preview
        initial_dir: Starting directory
        tool_tip: Enables file info tooltips
        **kwargs: Additional arguments passed to open()

    Returns:
        TextIOWrapper: Open file object in write mode, or None if canceled

    Example:
        >>> with asksaveasfile(mode='w', filetypes=['.jpeg', 'jpg', 'mp4'] as f:
        ...     if f:  # Check if not canceled
        ...         f.write("Log entry\\n")
    """
    app = DrawApp(filetypes=filetypes,
                  current_path=initial_dir,
                  hidden=hidden,
                  preview_img=preview_img,
                  method='asksaveasfile',
                  autocomplete=autocomplete,
                  video_preview=video_preview,
                  tool_tip=tool_tip)

    app.app.wait_window()
    
    return open(app.selected_file, mode=mode, **kwargs) if app.selected_file else None

def askopenfile(mode: Literal['r', 'rb', 'r+', 'rb+', 'r+b','w', 'wb', 'w+', 'wb+','a', 'ab', 'a+', 'ab+','x', 'xb'] = 'r',
                  hidden: bool = False,
                  filetypes: Optional[List[str]] = None,
                  preview_img: bool = False,
                  autocomplete: bool = False,
                  video_preview: bool = False,
                  initial_dir: str = str(Path.cwd()),
                  tool_tip: bool = False,
                  **kwargs,
                  ):
    """
    Displays an open file dialog and returns an open file object.

    Combines file selection with automatic file opening.
    The returned file object is ready for reading by default.

    Args:
        mode: File opening mode (defaults to 'r' for read)
        hidden: Shows hidden files when enabled
        filetypes: File type filters
        preview_img: Enables image preview
        autocomplete: Activates path completion
        video_preview: Enables video preview
        initial_dir: Starting directory
        tool_tip: Shows file info tooltips
        **kwargs: Additional arguments for open()

    Returns:
        TextIOWrapper: Open file object, or None if canceled

    Example:
        >>> f = askopenfile(mode='rb', filetypes=[".bin"])
        >>> if f:
        ...     data = f.read()
        ...     f.close()
    """
    app = DrawApp(filetypes=filetypes,
                  current_path=initial_dir,
                  hidden=hidden,
                  preview_img=preview_img,
                  method='askopenfile', 
                  autocomplete=autocomplete, 
                  video_preview=video_preview, 
                  tool_tip=tool_tip)

    app.app.wait_window()

    return open(app.selected_file, mode=mode, **kwargs) if app.selected_file else None

def askopenfiles(mode: Literal['r', 'rb', 'r+', 'rb+', 'r+b','w', 'wb', 'w+', 'wb+','a', 'ab', 'a+', 'ab+','x', 'xb'] = 'r',
                 hidden: bool = False,
                 filetypes: Optional[List[str]] = None,
                 preview_img: bool = False,
                 autocomplete: bool = False,
                 video_preview: bool = False,
                 initial_dir: str = str(Path.cwd()),
                 tool_tip: bool = False,
                 **kwargs,
                  ):
    """
    Displays a multi-file open dialog and returns multiple open file objects.

    Allows selection of multiple files and returns them as opened file objects.
    All files are opened with the same mode and kwargs.

    Args:
        mode: File opening mode for all files (default 'r')
        hidden: Shows hidden files when True
        filetypes: File extension filters
        preview_img: Enables image preview
        autocomplete: Activates path completion
        video_preview: Enables video preview
        initial_dir: Starting directory
        tool_tip: Shows file info tooltips
        **kwargs: Passed to each open() call

    Returns:
        tuple[TextIOWrapper]: Tuple of open file objects, or None if canceled

    Example:
        >>> files = askopenfiles(mode='r', filetypes=[".txt")])
        >>> if files:
        ...     for f in files:
        ...         print(f.read())
        ...         f.close()
    """
    app = DrawApp(filetypes=filetypes,
                  current_path=initial_dir, 
                  hidden=hidden,
                  preview_img=preview_img,
                  method='askopenfiles',
                  autocomplete=autocomplete,
                  video_preview=video_preview,
                  tool_tip=tool_tip)

    app.app.wait_window()
    
    return tuple(open(f, mode=mode, **kwargs) for f in app.selected_objects) if app.selected_objects else None
