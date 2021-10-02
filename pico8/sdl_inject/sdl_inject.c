#include <stdint.h>
#include <stdio.h>
#define _GNU_SOURCE
#define __GNU_SOURCE
#define __USE_GNU
#include <dlfcn.h>


#if 0
typedef int (*rect_set_func)(void*, uint32_t, uint32_t, uint32_t, uint32_t);

int vc_dispmanx_rect_set(void *rect, uint32_t x_offset, uint32_t y_offset, uint32_t width, uint32_t height )
{
    static rect_set_func orig_func = NULL;
    if (!orig_func)
    {
        orig_func = dlsym(RTLD_NEXT, "vc_dispmanx_rect_set");
    }

    printf("rect_set: %d,%d %d,%d", x_offset, y_offset, width, height);
    //return orig_func(rect, x_offset, y_offset, width, height);
    return -1;
}
#endif

typedef struct SDL_Rect
{
    int x, y;
    int w, h;
} SDL_Rect;

typedef int (*SDL_UpdateTexture_ptr)(void* texture, const SDL_Rect * rect, const void *pixels, int pitch);


int SDL_UpdateTexture(void* texture, const SDL_Rect * rect, const void *pixels, int pitch)
{
    static SDL_UpdateTexture_ptr orig_func = NULL;
    if (!orig_func)
    {
        orig_func = dlsym(RTLD_NEXT, "SDL_UpdateTexture");
    }

    printf("updateTex: %d,%d %d,%d", rect->x, rect->y, rect->w, rect->h);
    return orig_func(texture, rect, pixels, pitch);
    //return -1;

}


typedef struct SDL_Surface
{
    uint32_t flags;               /**< Read-only */
    void *format;    /**< Read-only */
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


typedef void (*SDL_UnlockSurface_ptr)(SDL_Surface *);

void SDL_UnlockSurface(SDL_Surface * surface)
{
    static SDL_UnlockSurface_ptr orig_func = NULL;
    if (!orig_func)
        orig_func = dlsym(RTLD_NEXT, "SDL_LockSurface");

    uint32_t* px = surface->pixels;
    printf("unlock: %d,%d px:%x %x %x %x %x %x %x %x %x\n", surface->w, surface->h, px[0],px[1],px[2],px[3],px[4],px[5],px[6],px[7],px[8]);
    orig_func(surface);
}
