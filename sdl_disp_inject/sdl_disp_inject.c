#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#define _GNU_SOURCE
#define __GNU_SOURCE
#define __USE_GNU
#include <dlfcn.h>

#include "../pico8/sdl_inject/sdl_default_keymap.h"
#include "../pico8/sdl_inject/sdl_event.h"


// LD_PRELOAD=/home/pi/led_console/sdl_disp_inject/sdl_disp_inject.so ./pico8_dyn

typedef int (*SDL_RenderCopy_ptr)(void*, void*, const void*, const void*);
typedef int (*SDL_RenderCopyEx_ptr)(void*, void*, const void*, const void*, const double, const void*, const int);

int SDL_RenderCopy(void * renderer, void * texture, const void * srcrect, const void * dstrect)
{
    //static SDL_RenderCopy_ptr orig_func = NULL;
    //if (!orig_func)
    //    orig_func = dlsym(RTLD_NEXT, "SDL_RenderCopy");
    static SDL_RenderCopyEx_ptr ex_func = NULL;
    if (!ex_func)
        ex_func = dlsym(RTLD_NEXT, "SDL_RenderCopyEx");

    return ex_func(renderer, texture, srcrect, dstrect, 90, NULL, 0);
}

#if 1
typedef int (*SDL_PollEvent_ptr)(SDL_Event*);

int g_test_btn = 5;

int SDL_PollEvent(SDL_Event * event)
{
    static SDL_PollEvent_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_PollEvent");
    int ret = orig_func(event);

    if (event->type == 0x650)
    {
        SDL_ControllerAxisEvent* cev = (SDL_ControllerAxisEvent*)event;
        printf("cont-axs: type:%x which: %d\n", cev->type, cev->which);
    }
    else if (event->type == 0x651 || event->type == 0x652)
    {
        SDL_ControllerButtonEvent* cev = (SDL_ControllerButtonEvent*)event;
        if (cev->which == 1)
            cev->which = 0;
        else if (cev->which == 0)
            cev->which = 1;
            
        if (cev->button == 5) {
            cev->button = 6;
        }
        printf("cont-btn: type:%x which: %d  btn:%d\n", cev->type, cev->which, cev->button);
    }

    return ret;
}
#endif

typedef void SDL_GameController;

typedef enum
{
    SDL_CONTROLLER_AXIS_INVALID = -1,
    SDL_CONTROLLER_AXIS_LEFTX,
    SDL_CONTROLLER_AXIS_LEFTY,
    SDL_CONTROLLER_AXIS_RIGHTX,
    SDL_CONTROLLER_AXIS_RIGHTY,
    SDL_CONTROLLER_AXIS_TRIGGERLEFT,
    SDL_CONTROLLER_AXIS_TRIGGERRIGHT,
    SDL_CONTROLLER_AXIS_MAX
} SDL_GameControllerAxis;

typedef SDL_GameController* (*SDL_GameControllerOpen_ptr)(int);

SDL_GameController* g_conts[2] = {0,0};

// need to swap joy 1 and joy 2 so that red is player 1
SDL_GameController* SDL_GameControllerOpen(int joystick_index)
{
    static SDL_GameControllerOpen_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_GameControllerOpen");
    if (joystick_index == 0)
        joystick_index = 1;
    else if (joystick_index == 1)
        joystick_index = 0;
    SDL_GameController* ret = orig_func(joystick_index);
    if (joystick_index == 0 || joystick_index == 1)
        g_conts[joystick_index] = ret;
    return ret;
}

typedef Sint16 (*SDL_GameControllerGetAxis_ptr)(SDL_GameController *, SDL_GameControllerAxis);

Sint16 SDL_GameControllerGetAxis(SDL_GameController *gamecontroller, SDL_GameControllerAxis axis)
{
    static SDL_GameControllerGetAxis_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_GameControllerGetAxis");

    Sint16 ret = orig_func(gamecontroller, axis);
    Sint16 orig_ret = ret;

    if (ret != 0 && ret != -1)
    {
        int idx = -1; 
        if (gamecontroller == g_conts[1]) // invert axis of player 2
        {
            idx = 1;
        }
        else if (gamecontroller == g_conts[0])
        {
            idx = 0;
            if (ret == -32768)
                ret = 32767;
            else if (ret == 32767)
                ret = -32768;
        }

        //printf("axis: idx:%d axis:%d ret:%d -> %d\n", idx, axis, orig_ret, ret);
    }

    return ret;
}

//SDL_GameControllerGetButton