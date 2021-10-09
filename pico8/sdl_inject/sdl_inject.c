#include <stdint.h>
#include <stdio.h>
#include <ncurses.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#define _GNU_SOURCE
#define __GNU_SOURCE
#define __USE_GNU
#include <dlfcn.h>

#include "sdl_default_keymap.h"
#include "sdl_event.h"
#include "event_queue.h"

#define WITH_NCURSES
#define DO_UNLOCKSURFACE
#define OVERRIDE_EVENTS
#define NO_WINDOW

char* g_textbuf = NULL;


__attribute__((constructor)) static void before_main(void) 
{

#ifdef WITH_NCURSES
    printf("at init\n");
    initscr();
	if(has_colors() == FALSE)
	{	
		endwin();
		printf("Your terminal does not support color\n");
		exit(1);
	}
	start_color();
	cbreak();
	keypad(stdscr, TRUE);
	noecho();
    curs_set(0);
    timeout(0);
#else
    printf("\x1b[?25l"); // hide cursor
#endif
    g_textbuf = (char*)malloc(20*128*128 + 6*126 + 3 + 1);
}

__attribute__((destructor)) static void after_main(void) 
{
    printf("at fini\n");
#ifdef WITH_NCURSES    
    endwin();
#endif    
}

typedef struct SDL_Rect
{
    int x, y;
    int w, h;
} SDL_Rect;

typedef struct SDL_PixelFormat
{
    Uint32 format;
    void *palette;
    Uint8 BitsPerPixel;
    Uint8 BytesPerPixel;
    Uint8 padding[2];
    Uint32 Rmask;
    Uint32 Gmask;
    Uint32 Bmask;
    Uint32 Amask;
    Uint8 Rloss;
    Uint8 Gloss;
    Uint8 Bloss;
    Uint8 Aloss;
    Uint8 Rshift;
    Uint8 Gshift;
    Uint8 Bshift;
    Uint8 Ashift;
    int refcount;
    struct SDL_PixelFormat *next;
} SDL_PixelFormat;

typedef struct SDL_Surface
{
    uint32_t flags;               /**< Read-only */
    SDL_PixelFormat *format;    /**< Read-only */
    int w, h;                   /**< Read-only */
    int pitch;                  /**< Read-only */
    void *pixels;               /**< Read-write */

    /** Application data associated with the surface */
    void *userdata;             /**< Read-write */

    /** information needed for surfaces requiring locks */
    int locked;                 /**< Read-only */

    /** list of BlitMap that hold a reference to this surface */
    void *list_blitmap;         /**< Private */

    /** clipping information */
    SDL_Rect clip_rect;         /**< Read-only */

    /** info for fast blit mapping to other surfaces */
    void *map;    /**< Private */

    /** Reference count -- used when freeing surface */
    int refcount;               /**< Read-mostly */
} SDL_Surface;

typedef int (*SDL_Init_ptr)(Uint32);
int SDL_Init(Uint32 flags)
{
    static SDL_Init_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_Init");
    printf("SDL_Init: %x\n", flags);
    flags &= ~0x20; // remove VIDEO
    return orig_func(flags);

    // called with
    // f231  everything...
    // 10 AUDIO
}

typedef int (*SDL_InitSubSystem_ptr)(Uint32 flags);
int SDL_InitSubSystem(Uint32 flags)
{
    static SDL_InitSubSystem_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_InitSubSystem");

    printf("SDL_InitSubSystem: %x\n", flags);
    return orig_func(flags);

    // called with
    // 10
}

const char* SDL_GetCurrentVideoDriver(void)
{
    return "x11";
}


#ifdef DO_UNLOCKSURFACE
typedef void (*SDL_UnlockSurface_ptr)(SDL_Surface *);

int g_frame_num = 0;

void SDL_UnlockSurface(SDL_Surface * surface)
{
    static SDL_UnlockSurface_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_UnlockSurface");

    uint32_t* px = surface->pixels;
    uint32_t c = px[0];
    uint32_t b = c & 0xff, 
            g = (c >> 8) & 0xff, 
            r = (c >> 16) && 0xff;
    //printf("unlock: %d,%d px:%x(%d,%d,%d) %x %x %x %x %x %x %x %x\n", surface->w, surface->h, px[0],r,g,b,px[1],px[2],px[3],px[4],px[5],px[6],px[7],px[8]);

    //printf("%d: start\n", g_frame_num);
    int offset = sprintf(g_textbuf, "\x1b[H"); // move to 1,1
	for(int y = 0, line = 0; y < 128; y += 2, ++line)
	{
		for(int x = 0; x < 128; ++x)
		{
            uint32_t fc = px[y * 128 + x];
            uint32_t fb = fc & 0xff, 
                     fg = (fc >> 8) & 0xff, 
                     fr = (fc >> 16) & 0xff;
            uint32_t bc = px[(y+1) * 128 + x];
            uint32_t bb = bc & 0xff, 
                     bg = (bc >> 8) & 0xff, 
                     br = (bc >> 16) & 0xff;

			offset += sprintf(g_textbuf + offset, "\x1b[38;2;%d;%d;%dm\x1b[48;2;%d;%d;%dm\u2580", fr, fg, fb, br, bg, bb);
		}
		offset += sprintf(g_textbuf + offset, "\x1b[%dH", line+1);
	}
    offset += sprintf(g_textbuf + offset, "\x1b[0m"); // reset color
    //printf("%d: did buf %d\n", g_frame_num, offset);

	write(1, g_textbuf, offset);

    //printf("%d: wrote\n", g_frame_num);
    ++g_frame_num;

    // orig_func(surface);
}

int SDL_LockSurface(SDL_Surface * surface)
{
    return 0;
}

typedef int SDL_Window;

typedef void (*SDL_GetWindowSize_ptr)(SDL_Window * window, int *w, int *h);

void SDL_GetWindowSize(SDL_Window * window, int *w, int *h)
{
/*    static SDL_GetWindowSize_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_GetWindowSize");*/
    *w = 128;
    *h = 128;
    //orig_func(window, w, h);
    //printf("SDL_GetWindowSize: (%d) %d, %d\n", calls++, *w, *h);
};

int SDL_UpdateWindowSurface(SDL_Window * window)
{
    return 0;
}

Uint32 SDL_GetWindowID(SDL_Window * window)
{
    printf("SDL_GetWindowID call\n");
    return 0;
}

SDL_Window * SDL_GetKeyboardFocus(void)
{
    printf("SDL_GetKeyboardFocus call\n");
    return NULL;
}

SDL_PixelFormat myFormat;
SDL_Surface mySurf;


//surface: f:5 w:128 h:128 p:512 u:(nil) l:0 b:(nil) m:0x1dfccf8 rc:1
 //        rect: 0 0 128 128
 //        format: 16161804 p:(nil), bpp:32 Bpp:4, r:ff0000 g:ff00 b:ff
 //        format: 16161804 // SDL_PIXELFORMAT_RGB888


typedef SDL_Surface * (*SDL_GetWindowSurface_ptr)(SDL_Window * window);
SDL_Surface * SDL_GetWindowSurface(SDL_Window * window)
{
    static int count = 0;

#if 0    
    static SDL_GetWindowSurface_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_GetWindowSurface");

    SDL_Surface* ret = orig_func(window);

    printf("surface (%d): f:%d w:%d h:%d p:%d u:%p l:%d b:%p m:%p rc:%d\n", count++, ret->flags, ret->w, ret->h, ret->pitch, ret->userdata, ret->locked, ret->list_blitmap, ret->map, ret->refcount);
    printf("         rect: %d %d %d %d\n", ret->clip_rect.x, ret->clip_rect.y, ret->clip_rect.w, ret->clip_rect.h);
    printf("         format: %x p:%p, bpp:%d Bpp:%d, r:%x g:%x b:%x\n", ret->format->format, ret->format->palette, ret->format->BitsPerPixel, ret->format->BytesPerPixel, ret->format->Rmask, ret->format->Gmask, ret->format->Bmask);
    return ret;
#endif

    static bool inited = false;
    //printf("SDL_GetWindowSurface call %d\n", count++);
    if (!inited)
    {
        memset(&mySurf, 0, sizeof(mySurf));
        mySurf.w = 128;
        mySurf.h = 128;
        mySurf.pitch = 512;
        mySurf.pixels = malloc(128*128*sizeof(uint32_t));
        mySurf.format = &myFormat;
        mySurf.clip_rect.w = 128;
        mySurf.clip_rect.h = 128;
        mySurf.refcount = 1;

        memset(&myFormat, 0, sizeof(myFormat));
        myFormat.format = 0x16161804; // SDL_PIXELFORMAT_RGB888
        myFormat.BitsPerPixel = 32;
        myFormat.BytesPerPixel = 4;
        myFormat.Rmask = 0xff0000;
        myFormat.Gmask = 0xff00;
        myFormat.Bmask = 0xff;
        inited = true;
    }
    return &mySurf;
}
#endif

#ifdef NO_WINDOW

SDL_Window myWnd;
SDL_Window * SDL_CreateWindow(const char *title, int x, int y, int w, int h, Uint32 flags)
{
    printf("SDL_CreateWindow %s, %d %d %d %d  %x\n", title, x, y, w, h, flags);
    return &myWnd;
}

#endif




// ------------------ keyboard ----------------

// this is needed for the X-Server bug so that Ctrl+Q works
typedef int (*SDL_GetKeyFromScancode_ptr)(int);
typedef void (*SDL_ResetKeyboard_ptr)(void);

int SDL_GetKeyFromScancode(int scancode)
{
    static SDL_GetKeyFromScancode_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_GetKeyFromScancode");
   

    if (((int)scancode) < SDL_SCANCODE_UNKNOWN || scancode >= SDL_NUM_SCANCODES) {
          return 0;
    }
    //int ret = orig_func(scancode);

    int ret2 = SDL_default_keymap[scancode];

    //printf("  scancode: %d  keycode: %d\n", scancode, ret2);
    return ret2;
}


typedef Uint32 (*SDL_GetTicks_ptr)(void);

SDL_GetTicks_ptr SDL_GetTicks_my;


struct EventQueue g_eventQueue;

void push_key_down_up(int c, int s)
{
    Uint32 now = SDL_GetTicks_my();

    SDL_Event* newe = queue_enq(&g_eventQueue);
    if (newe == NULL)
        return;
    newe->type = SDL_KEYDOWN;
    newe->key.timestamp = now; //event->key.timestamp;
    newe->key.state = SDL_PRESSED;
    newe->key.keysym.sym = (char)c;
    newe->key.keysym.scancode = s;
    newe->key.windowID = 0;
    newe->key.keysym.mod = 0;

    newe = queue_enq(&g_eventQueue);
    if (newe == NULL)
        return;
    newe->type = SDL_KEYUP;
    newe->key.timestamp = now + 100; //event->key.timestamp;
    newe->key.state = SDL_RELEASED;
    newe->key.keysym.sym = (char)c;
    newe->key.keysym.scancode = s;
    newe->key.windowID = 0;
    newe->key.keysym.mod = 0;
}
void push_text_input(int c)
{
    SDL_Event* newe = queue_enq(&g_eventQueue);
    if (newe == NULL)
        return;

    newe->type = SDL_TEXTINPUT;
    newe->text.timestamp = 0; //event->key.timestamp;
    newe->text.text[0] = (char)c;
    newe->text.text[1] = 0;
    newe->text.windowID = 0;
}

void enq_keyboard(void)
{
    int c = getch(); // should not be blocking due to timeout() above
    if (c == ERR)
        return;
    if (c >= 'a' && c <= 'z')
    {
        push_key_down_up(c, SDL_SCANCODE_A + (c - 'a'));
        push_text_input(c);
    }
    else if (c >= 'A' && c <= 'Z')
    {
        push_key_down_up(c, SDL_SCANCODE_A + (c - 'A'));
        push_text_input(c);
    }

}

#ifdef OVERRIDE_EVENTS

int SDL_PollEvent(SDL_Event * event)
{
    static bool inited = false;
    if (!inited) {
        SDL_GetTicks_my = dlsym(RTLD_DEFAULT, "SDL_GetTicks");
        queue_init(&g_eventQueue, 100);
        inited = true;
    }


    enq_keyboard();

    SDL_Event* mye = queue_deq(&g_eventQueue);
    if (mye != NULL)
    {
//        printf("event %x\n", mye->type);
        memcpy(event, mye, sizeof(SDL_Event));

        printf("event %x ts:%d w:%d st:%d rep:%d  scancode:%d  keycode:%d  mod:%d\n", event->type, event->key.timestamp, event->key.windowID, event->key.state, event->key.repeat, event->key.keysym.scancode,  event->key.keysym.sym, event->key.keysym.mod);

        return 1;
    }
    return 0;
}

#else

// event 300 ts:10483,10483 w:2 st:1 rep:0  scancode: 9  keycode: 102,102  mod:0
//event 301 ts:10551,10551 w:2 st:0 rep:0  scancode: 9  keycode: 102,102  mod:0

typedef int (*SDL_PollEvent_ptr)(SDL_Event *);
int SDL_PollEvent(SDL_Event * event)
{
    static SDL_PollEvent_ptr orig_func = NULL;
    if (!orig_func) {
        orig_func = dlsym(RTLD_NEXT, "SDL_PollEvent");
        queue_init(&g_eventQueue, 100);
        SDL_GetTicks_my = dlsym(RTLD_DEFAULT, "SDL_GetTicks");
    }
 
    int ret = orig_func(event);
    if (ret != 0)
    {
        if (event->type == SDL_KEYDOWN || event->type == SDL_KEYUP)
        {
            int orig = event->key.keysym.sym;
            event->key.keysym.sym = SDL_default_keymap[event->key.keysym.scancode];

            printf("event %x ts:%d,%d w:%d st:%d rep:%d  scancode: %d  keycode: %d,%d  mod:%d\n", event->type, event->key.timestamp, SDL_GetTicks_my(), event->key.windowID, event->key.state, event->key.repeat, event->key.keysym.scancode,  event->key.keysym.sym, orig, event->key.keysym.mod);
            // This fixes the bug that happens when running through an remote X server from Windows with an additional keyboard langauge installed
            // The keycode is wrong and TEXTINPUT events are not generated
            if (event->type == SDL_KEYDOWN && orig > 256)
            {
                SDL_Event* newe = queue_enq(&g_eventQueue);
                if (newe != NULL)
                {
                    newe->type = SDL_TEXTINPUT;
                    newe->text.timestamp = event->key.timestamp;
                    newe->text.text[0] = event->key.keysym.sym;
                    newe->text.text[1] = 0;
                    newe->text.windowID = event->key.windowID;
                    //printf("  enq my %p  %d,%d\n", newe, g_eventQueue.rear, g_eventQueue.front);
                }
            }
        }
        else if (event->type == SDL_TEXTINPUT)
        {
            //printf("event %x   ", event->type);
            int i = 0;
            while (event->edit.text[i] != 0)
                printf(" %d", event->text.text[i++]);
            printf("\n");
        }
        else
        {
            //printf("event %x\n", event->type);
            if (event->type == 0x200)
                return 1;
            return 0;
        }
    }
    else // check my queue
    {
        SDL_Event* mye = queue_deq(&g_eventQueue);
        if (mye != NULL)
        {
            //printf("  deq my %p\n", mye);
            //printf("MY-event %x text: %d %d\n", mye->type, mye->text.text[0], mye->text.text[1]);
            memcpy(event, mye, sizeof(SDL_Event));
            //printf("CP-event %x text: %d %d\n", event->type, event->text.text[0], event->text.text[1]);
            return 1;
        }
    }

    return ret;
}
#endif

#if 0
typedef uint8_t* (*SDL_GetKeyboardState_ptr)(int*);

const uint8_t* SDL_GetKeyboardState(int *numkeys)
{
    static SDL_GetKeyboardState_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_GetKeyboardState");

    printf("SDL_GetKeyboardState called\n");
    uint8_t* ret = orig_func(numkeys);

    return ret;   
}
#endif