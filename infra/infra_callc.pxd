
from cpython cimport array
from libc.stdint cimport uintptr_t

cdef class IntMatrix:
    cdef int w
    cdef int h
    cdef array.array d_mem
    cdef unsigned int[:] d

    cpdef reset(self)
    cpdef set(self, int x, int y, unsigned int c)
    cpdef unsigned int get(self, int x, int y)
    cpdef unsigned int mget(self, int x, int y)
    cpdef fill(self, unsigned int v)
    cpdef scale_to_screen(self, uintptr_t scr_ptr, int scr_width, int scr_height)
    cpdef blit_from(self, IntMatrix src, int src_x, int src_y, int dst_x, int dst_y, int mw, int mh)