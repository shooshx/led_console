
from cpython cimport array
from libc.stdint cimport uintptr_t

cdef class IntMatrix:
    cdef int w
    cdef int h
    cdef array.array d_mem
    cdef unsigned int[:] d

    cpdef reset(self)
    cpdef set(self, int x, int y, unsigned int c)
    cpdef mset(self, int x, int y, unsigned int c)
    cpdef unsigned int get(self, int x, int y)
    cpdef unsigned int mget(self, int x, int y)
    cpdef fill(self, unsigned int v)
    cpdef scale_to_screen(self, uintptr_t scr_ptr, int scr_width, int scr_height)
    cpdef blit_from(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh)
    cpdef mblit_from(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh)

    cpdef int width(self)
    cpdef int height(self)
    cpdef get_memview(self)


cdef class Color:
    cdef int r, g, b

    cdef int reset(self)
    cdef int add(self, unsigned int c)
    cdef int set(self, unsigned int c)
    cdef int div(self, int n)
    cdef int mult(self, float n)
    cdef int hsv_stretch(self)
    cdef unsigned int as_uint(self)
    cdef unsigned int as_uint_max(self)


cdef (float, float, float) hsv_to_rgb(float h, float s, float v)