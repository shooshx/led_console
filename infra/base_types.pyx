import array
import PIL.Image

from libc.string cimport memset
from libc.stdint cimport uintptr_t



cpdef mat_from_image(str filename):
    cdef object img, img_data
    cdef IntMatrix mat
    cdef int i, r, g, b, a
    cdef unsigned int col
    img = PIL.Image.open(filename)
    img_data = img.getdata()
    mat = IntMatrix(img.width, img.height)
    assert(img.mode == "RGBA")
    i = 0
    for b, g, r, a in img_data:
        col = r | (g << 8) | (b << 16) | (a << 24)
        mat.d[i] = col
        i += 1
    return mat


cdef class IntMatrix:
    #cdef int w
    #cdef int h
    #cdef array.array d_mem
    ##cdef unsigned int[:] d
    #cdef unsigned int* d
    def __init__(self, int w, int h):
        self.w = w
        self.h = h
        self.reset()

    cpdef int width(self):
        return self.w
    cpdef int height(self):
        return self.h
    cpdef get_memview(self):
        return memoryview(self.d_mem)

    cpdef reset(self):
        #self.MatType = ctypes.c_uint32 * (self.w * self.h)
        self.d_mem = array.array('I', [0]*(self.w*self.h))
        #self.d = self.d_mem
        self.d = self.d_mem.data.as_uints

    cpdef reset_raw_ptr(self, uintptr_t d):
        self.d_mem = None
        self.d = <unsigned int*>d

    cpdef uintptr_t get_raw_ptr(self):
        return <uintptr_t>self.d

    cdef c_set(self, int x, int y, unsigned int c):
        assert x >= 0 and x < self.w and y >= 0 and y < self.h, f"access out of bounds"
        self.d[y * self.w + x] = c
    cpdef set(self, int x, int y, unsigned int c):
        assert x >= 0 and x < self.w and y >= 0 and y < self.h, f"access out of bounds"
        self.d[y * self.w + x] = c        

    cdef c_uset(self, int x, int y, unsigned int c):
        self.d[y * self.w + x] = c
    cpdef uset(self, int x, int y, unsigned int c):
        self.d[y * self.w + x] = c

    cdef c_mset(self, int x, int y, unsigned int c):
        self.d[(y % self.h) * self.w + (x % self.w)] = c  # TODO bitwise
    cpdef mset(self, int x, int y, unsigned int c):
        self.d[(y % self.h) * self.w + (x % self.w)] = c  # TODO bitwise

    cpdef madd_alpha(self, int x, int y, unsigned int c, float f):
        cdef unsigned char* p
        cdef float a, oma
        cdef int r, g, b

        a = (float(c >> 24) / 255.0) * f
        r = int((c & 0xff) * a)
        g = int(((c >> 8) & 0xff) * a)
        b = int(((c >> 16) & 0xff) * a)
        oma = 1.0 - a

        p = <unsigned char*>&self.d[(y % self.h) * self.w + (x % self.w)]
        p[0] = int(p[0] * oma) + r
        p[1] = int(p[1] * oma) + g
        p[2] = int(p[2] * oma) + b

    cdef unsigned int c_get(self, int x, int y):
        return self.d[y * self.w + x]
    cpdef unsigned int get(self, int x, int y):
        return self.d[y * self.w + x]        
      
    cdef unsigned int c_mget(self, int x, int y):
        return self.d[(y % self.h) * self.w + (x % self.w)]
    cpdef unsigned int mget(self, int x, int y):
        return self.d[(y % self.h) * self.w + (x % self.w)]



    cpdef fill(self, unsigned int v):
        memset(self.d_mem.data.as_voidptr, v, len(self.d_mem) * sizeof(int))

    cpdef scale_to_screen(self, uintptr_t scr_ptr_i, int scr_width, int scr_height):
        cdef int scale, fill_width, sides_margin, side_margin, fill_height, top_margin
        cdef int p, px, py, yi, xi
        cdef unsigned int* scr_ptr = <unsigned int*>scr_ptr_i

        memset(scr_ptr, 0x20, scr_width*scr_height*4)

        if scr_width > scr_height:
            scale = scr_height // self.h
        else:
            scale = scr_width // self.w
        fill_width = self.w * scale
        sides_margin = (scr_width - fill_width)
        side_margin = (scr_width - fill_width) // 2
        fill_height = self.h * scale
        top_margin = (scr_height - fill_height) // 2

        p = top_margin * scr_width + side_margin

        for py in range(0, self.h):
            for yi in range(0, scale):
                for px in range(0, self.w):
                    c = self.d[py * self.w + px]
                    for xi in range(0, scale):
                        scr_ptr[p] = c
                        p += 1
                p += sides_margin

    cpdef blit_from(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh):
        cdef int x, y
        for y in range(0, mh):
            for x in range(0, mw):
                self.c_set(dst_x + x, dst_y + y, src.c_get(x + src_x, y + src_y))

    # for sprites
    cpdef blit_from_sp(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh, float f):
        cdef int x, y
        cdef unsigned int c

        for y in range(0, mh):
            for x in range(0, mw):
                c = src.c_get(x + src_x, y + src_y)
                #if c & 0xff000000 == 0:
                #    self.mset(dst_x + x, dst_y + y, 0xffffffff)

                self.madd_alpha(dst_x + x, dst_y + y, c, f)

    cpdef mblit_from(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh):
        cdef int x, y
        for y in range(0, mh):
            for x in range(0, mw):
                self.c_set(dst_x + x, dst_y + y, src.mget(x + src_x, y + src_y))

    def rect_fill(self, int xstart, int ystart, int w, int h, unsigned int c):
        cdef int xend, yend, yi, xi
        xend = xstart + w
        yend = ystart + h
        for yi in range(ystart, yend):
            for xi in range(xstart, xend):
                self.c_set(xi, yi, c)

    def rect_fill_a(self, int xstart, int ystart, int w, int h, unsigned int c):
        cdef int xend, yend, yi, xi
        xend = xstart + w
        yend = ystart + h
        for yi in range(ystart, yend):
            for xi in range(xstart, xend):
                self.madd_alpha(xi, yi, c, 1.0)

    cpdef hline(self, int xstart, int xend, int y, unsigned int c):
        cdef int xi
        for xi in range(xstart, xend+1):
            self.c_set(xi, y, c)

    cpdef vline(self, int x, int ystart, int yend, unsigned int c):
        cdef int yi
        for yi in range(ystart, yend+1):
            self.c_set(x, yi, c)

# from Lib
cdef float rgb_to_h(float r, float g, float b):
    cdef float maxc, minc, v, s, rc, gc, bc, h
    maxc = max(r, g, b)
    minc = min(r, g, b)
    v = maxc
    if minc == maxc:
        return v
    s = (maxc-minc) / maxc
    rc = (maxc-r) / (maxc-minc)
    gc = (maxc-g) / (maxc-minc)
    bc = (maxc-b) / (maxc-minc)
    if r == maxc:
        h = bc-gc
    elif g == maxc:
        h = 2.0+rc-bc
    else:
        h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h

cdef (float, float, float) hsv_to_rgb(float h, float s, float v):
    cdef float f, p, q, t
    cdef int i
    if s == 0.0:
        return v, v, v
    i = int(h*6.0) # XXX assume int() truncates!
    f = (h*6.0) - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0-f))
    i = i%6
    if i == 0:
        return v, t, p
    if i == 1:
        return q, v, p
    if i == 2:
        return p, v, t
    if i == 3:
        return p, q, v
    if i == 4:
        return t, p, v
    if i == 5:
        return v, p, q
    # Cannot get here

cdef class Color:
    #cdef int r, g, b
    def __init__(self):
        self.r = 0
        self.g = 0
        self.b = 0
    cdef int reset(self):
        self.r = 0
        self.g = 0
        self.b = 0
        return 0
    cdef int add(self, unsigned int c):
        self.r += c & 0xff
        self.g += (c >> 8) & 0xff
        self.b += (c >> 16) & 0xff
        return 0
    cdef int set(self, unsigned int c):
        self.r = c & 0xff
        self.g = (c >> 8) & 0xff
        self.b = (c >> 16) & 0xff
        return 0
    cdef int div(self, int n):
        self.r /= n
        self.g /= n
        self.b /= n
        return 0
    cdef int mult(self, float n):
        self.r = int(float(self.r) * n)
        self.g = int(float(self.g) * n)
        self.b = int(float(self.b) * n)
        return 0


    cdef int hsv_stretch(self):
        cdef float h, s, v, r, g, b
        if self.r == 255 and self.g == 255 and self.b == 255:
            return 0
        h = rgb_to_h(float(self.r) / 255.0, float(self.g) / 255.0, float(self.b) / 255.0)
        r,g,b = hsv_to_rgb(h, 1.0, 1.0)
        self.r = int(r * 255)
        self.g = int(g * 255)
        self.b = int(b * 255)
        return 0

    cdef unsigned int as_uint(self):
        return self.r | (self.g << 8) | (self.b << 16)

    cdef unsigned int as_uint_max(self):
        return min(self.r,255) | (min(self.g,255) << 8) | (min(self.b,255) << 16)
