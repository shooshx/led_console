from cpython cimport array
from libc.stdint cimport uintptr_t

cdef class IntMatrix:
    cdef int w
    cdef int h
    cdef array.array d_mem
    #cdef unsigned int[:] d
    cdef unsigned int* d

    cpdef reset(self)
    cpdef reset_raw_ptr(self, uintptr_t d)
    cpdef uintptr_t get_raw_ptr(self)

    cdef c_set(self, int x, int y, unsigned int c)
    cpdef set(self, int x, int y, unsigned int c)
    cdef c_uset(self, int x, int y, unsigned int c)
    cpdef uset(self, int x, int y, unsigned int c)
    cdef c_mset(self, int x, int y, unsigned int c)
    cpdef mset(self, int x, int y, unsigned int c)
    cdef c_iset(self, int x, int y, unsigned int c)
    cpdef iset(self, int x, int y, unsigned int c)

    cpdef madd_alpha(self, int x, int y, unsigned int c, float f)
    cdef unsigned int c_get(self, int x, int y)
    cpdef unsigned int get(self, int x, int y)
    cdef unsigned int c_mget(self, int x, int y)
    cpdef unsigned int mget(self, int x, int y)
    cpdef fill(self, unsigned int v)

    cpdef blit_from(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh)
    cpdef mblit_from(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh)
    cpdef blit_from_sp(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh, float f)

    cpdef hline(self, int xstart, int xend, int y, unsigned int c) # inclusive
    cpdef vline(self, int x, int ystart, int yend, unsigned int c)
    cpdef ihline(self, int xstart, int xend, int y, unsigned int c)
    cpdef ivline(self, int x, int ystart, int yend, unsigned int c)

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

cpdef unsigned int rand_color()