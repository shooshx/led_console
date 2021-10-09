sudo apt-get install libncurses5-dev

https://pico-8.fandom.com/wiki/RunningPico8

LD_PRELOAD=../sdl_inject/sdl_inject.so ./pico8_dyn -width 128 -height 128 -windowed 1


log at /home/pi/.lexaloffle/pico-8

SDL_DYNAPI_entry
SDL_GetTicks
SDL_DYNAPI_entry
SDL_SetHint
V SDL_Init
SDL_GetVersion
V SDL_GetCurrentVideoDriver
SDL_GL_SetAttribute
SDL_GetDesktopDisplayMode
SDL_GameControllerAddMapping
SDL_NumJoysticks
SDL_CreateWindow
SDL_CreateRGBSurfaceFrom
SDL_SetWindowIcon
SDL_FreeSurface
SDL_LockAudio
SDL_UnlockAudio
V SDL_InitSubSystem
SDL_OpenAudio
SDL_PauseAudio
SDL_GetNumAudioDrivers
SDL_GetAudioDriver
SDL_GetCurrentAudioDriver
SDL_Delay
SDL_ShowCursor
SDL_GetKeyboardState
SDL_GetModState
V SDL_PollEvent
SDL_GetMouseState
V SDL_GetWindowSize
V SDL_GetWindowSurface
V SDL_LockSurface
V SDL_UnlockSurface
V SDL_UpdateWindowSurface  - this is what actually pushes pixels to the screen
V SDL_GetWindowID
V SDL_GetKeyboardFocus
SDL_GetKeyFromScancode
SDL_DestroyWindow
SDL_VideoQuit
