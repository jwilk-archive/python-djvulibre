# Copyright © 2007, 2008 Jakub Wilk <ubanus@users.sf.net>

cdef extern from 'stdio.h':
	ctypedef struct FILE

from djvu.sexpr cimport cexpr_t, _WrappedCExpr
from djvu.sexpr cimport public_c2py as cexpr2py
from djvu.sexpr cimport public_py2c as py2cexpr

cdef extern from 'libdjvu/ddjvuapi.h':
	struct ddjvu_context_s
	struct ddjvu_message_s
	struct ddjvu_job_s
	struct ddjvu_document_s
	struct ddjvu_page_s
	struct ddjvu_format_s
	struct ddjvu_rect_s
	struct ddjvu_rectmapper_s

	ctypedef ddjvu_context_s ddjvu_context_t
	ctypedef ddjvu_message_s ddjvu_message_t
	ctypedef ddjvu_job_s ddjvu_job_t
	ctypedef ddjvu_document_s ddjvu_document_t
	ctypedef ddjvu_page_s ddjvu_page_t
	ctypedef ddjvu_format_s ddjvu_format_t
	ctypedef ddjvu_rect_s ddjvu_rect_t
	ctypedef ddjvu_rectmapper_s ddjvu_rectmapper_t

	ddjvu_context_t* ddjvu_context_create(char* program_name) nogil
	void ddjvu_context_release(ddjvu_context_t* context) nogil

	void ddjvu_cache_set_size(ddjvu_context_t* context, unsigned long cachesize) nogil
	unsigned long ddjvu_cache_get_size(ddjvu_context_t* context) nogil
	void ddjvu_cache_clear(ddjvu_context_t* context) nogil
	
	ddjvu_message_t* ddjvu_message_peek(ddjvu_context_t* context) nogil
	ddjvu_message_t* ddjvu_message_wait(ddjvu_context_t* context) nogil
	void ddjvu_message_pop(ddjvu_context_t* context) nogil

	ctypedef void (*ddjvu_message_callback_t)(ddjvu_context_t* context, void* closure) nogil

	void ddjvu_message_set_callback(ddjvu_context_t* context, ddjvu_message_callback_t callback, void* closure) nogil

	cdef enum ddjvu_status_e:
		DDJVU_JOB_NOTSTARTED
		DDJVU_JOB_STARTED
		DDJVU_JOB_OK
		DDJVU_JOB_FAILED
		DDJVU_JOB_STOPPED
	ctypedef ddjvu_status_e ddjvu_status_t

	ddjvu_status_t ddjvu_job_status(ddjvu_job_t* job) nogil
	int ddjvu_job_done(ddjvu_job_t* job) nogil
	int ddjvu_job_error(ddjvu_job_t* job) nogil
	void ddjvu_job_stop(ddjvu_job_t* job) nogil
	void ddjvu_job_set_user_data(ddjvu_job_t* job, void* userdata) nogil
	void* ddjvu_job_get_user_data(ddjvu_job_t* job) nogil
	void ddjvu_job_release(ddjvu_job_t* job) nogil

	cdef enum ddjvu_message_tag_t:
		DDJVU_ERROR
		DDJVU_INFO
		DDJVU_NEWSTREAM
		DDJVU_DOCINFO
		DDJVU_PAGEINFO
		DDJVU_RELAYOUT
		DDJVU_REDISPLAY
		DDJVU_CHUNK
		DDJVU_THUMBNAIL
		DDJVU_PROGRESS

	cdef struct ddjvu_message_any_s:
		ddjvu_message_tag_t tag
		ddjvu_context_t* context
		ddjvu_document_t* document
		ddjvu_page_t* page
		ddjvu_job_t* job
	ctypedef ddjvu_message_any_s ddjvu_message_any_t

	cdef struct ddjvu_message_error_s:
		ddjvu_message_any_t any
		char* message
		char* function
		char* filename
		int lineno

	cdef struct ddjvu_message_info_s:
		ddjvu_message_any_t any
		char* message

	ddjvu_document_t* ddjvu_document_create(ddjvu_context_t* context, char* url, int cache) nogil
	ddjvu_document_t* ddjvu_document_create_by_filename(ddjvu_context_t* context, char* filename, int cache) nogil
	ddjvu_job_t* ddjvu_document_job(ddjvu_document_t* document) nogil
	void ddjvu_document_release(ddjvu_document_t* document) nogil

	void ddjvu_document_set_user_data(ddjvu_document_t* document, void* userdata) nogil
	void* ddjvu_document_get_user_data(ddjvu_document_t* document) nogil

	ddjvu_status_t ddjvu_document_decoding_status(ddjvu_document_t* document) nogil
	int ddjvu_document_decoding_done(ddjvu_document_t* document) nogil
	int ddjvu_document_decoding_error(ddjvu_document_t* document) nogil

	cdef struct ddjvu_message_newstream_s:
		ddjvu_message_any_t any
		int streamid
		char* name
		char* url

	void ddjvu_stream_write(ddjvu_document_t* document, int streamid, char* data, unsigned long datalen) nogil
	void ddjvu_stream_close(ddjvu_document_t* document, int streamid, int stop) nogil

	cdef struct ddjvu_message_docinfo_s:
		ddjvu_message_any_t any

	cdef enum ddjvu_document_type_t:
		DDJVU_DOCTYPE_UNKNOWN
		DDJVU_DOCTYPE_SINGLEPAGE
		DDJVU_DOCTYPE_BUNDLED
		DDJVU_DOCTYPE_INDIRECT
		DDJVU_DOCTYPE_OLD_BUNDLED
		DDJVU_DOCTYPE_OLD_INDEXED

	ddjvu_document_type_t ddjvu_document_get_type(ddjvu_document_t* document) nogil
	int ddjvu_document_get_pagenum(ddjvu_document_t* document) nogil
	int ddjvu_document_get_filenum(ddjvu_document_t* document) nogil

	cdef struct ddjvu_fileinfo_s:
		char type
		int pageno
		int size
		char* id
		char* name
		char* title
	ctypedef ddjvu_fileinfo_s ddjvu_fileinfo_t

	ddjvu_status_t ddjvu_document_get_fileinfo(ddjvu_document_t* document, int fileno, ddjvu_fileinfo_t* info) nogil
	int ddjvu_document_check_pagedata(ddjvu_document_t* document, int pageno) nogil

	cdef struct ddjvu_pageinfo_s:
		int width
		int height
		int dpi
		int rotation
		int version
	ctypedef ddjvu_pageinfo_s ddjvu_pageinfo_t

	ddjvu_status_t ddjvu_document_get_pageinfo(ddjvu_document_t* document, int pageno, ddjvu_pageinfo_t* info) nogil
	ddjvu_status_t ddjvu_document_get_pageinfo_imp(ddjvu_document_t* document, int pageno, ddjvu_pageinfo_t* info, unsigned int infosz) nogil
	char* ddjvu_document_get_pagedump(ddjvu_document_t* document, int pageno) nogil
	char* ddjvu_document_get_filedump(ddjvu_document_t* document, int fileno) nogil

	ddjvu_page_t* ddjvu_page_create_by_pageno(ddjvu_document_t* document, int pageno) nogil
	ddjvu_job_t* ddjvu_page_job(ddjvu_page_t* page) nogil

	void ddjvu_page_release(ddjvu_page_t* page) nogil
	void ddjvu_page_set_user_data(ddjvu_page_t* page, void* userdata) nogil
	void* ddjvu_page_get_user_data(ddjvu_page_t* page) nogil

	ddjvu_status_t ddjvu_page_decoding_status(ddjvu_page_t* page) nogil
	int ddjvu_page_decoding_done(ddjvu_page_t* page) nogil
	int ddjvu_page_decoding_error(ddjvu_page_t* page) nogil

	cdef struct ddjvu_message_pageinfo_s:
		ddjvu_message_any_t any

	cdef struct ddjvu_message_relayout_s:
		ddjvu_message_any_t any

	cdef struct ddjvu_message_redisplay_s:
		ddjvu_message_any_t any

	cdef struct ddjvu_message_chunk_s:
		ddjvu_message_any_t any
	char* chunkid

	int ddjvu_page_get_width(ddjvu_page_t* page) nogil
	int ddjvu_page_get_height(ddjvu_page_t* page) nogil
	int ddjvu_page_get_resolution(ddjvu_page_t* page) nogil
	double ddjvu_page_get_gamma(ddjvu_page_t* page) nogil
	int ddjvu_page_get_version(ddjvu_page_t* page) nogil
	int ddjvu_code_get_version()

	cdef enum ddjvu_page_type_s:
		DDJVU_PAGETYPE_UNKNOWN
		DDJVU_PAGETYPE_BITONAL
		DDJVU_PAGETYPE_PHOTO
		DDJVU_PAGETYPE_COMPOUND
	ctypedef ddjvu_page_type_s ddjvu_page_type_t

	ddjvu_page_type_t ddjvu_page_get_type(ddjvu_page_t* page) nogil

	cdef enum ddjvu_page_rotation_s:
		DDJVU_ROTATE_0
		DDJVU_ROTATE_90
		DDJVU_ROTATE_180
		DDJVU_ROTATE_270
	ctypedef ddjvu_page_rotation_s ddjvu_page_rotation_t

	void ddjvu_page_set_rotation(ddjvu_page_t* page, ddjvu_page_rotation_t rot) nogil
	ddjvu_page_rotation_t ddjvu_page_get_rotation(ddjvu_page_t* page) nogil
	ddjvu_page_rotation_t ddjvu_page_get_initial_rotation(ddjvu_page_t* page) nogil

	cdef enum ddjvu_render_mode_s:
		DDJVU_RENDER_COLOR
		DDJVU_RENDER_BLACK
		DDJVU_RENDER_COLORONLY
		DDJVU_RENDER_MASKONLY
		DDJVU_RENDER_BACKGROUND
		DDJVU_RENDER_FOREGROUND
	ctypedef int ddjvu_render_mode_t

	cdef struct ddjvu_rect_s:
		int x, y
		unsigned int w, h

	int ddjvu_page_render(ddjvu_page_t* page, ddjvu_render_mode_t mode, ddjvu_rect_t* pagerect, ddjvu_rect_t* renderrect, ddjvu_format_t* pixelformat, unsigned long rowsize, char* imagebuffer) nogil

	ddjvu_rectmapper_t* ddjvu_rectmapper_create(ddjvu_rect_t* input, ddjvu_rect_t* output) nogil
	void ddjvu_rectmapper_modify(ddjvu_rectmapper_t* mapper, int rotation, int mirrorx, int mirrory) nogil
	void ddjvu_rectmapper_release(ddjvu_rectmapper_t* mapper) nogil
	void ddjvu_map_point(ddjvu_rectmapper_t* mapper, int* x, int* y) nogil
	void ddjvu_map_rect(ddjvu_rectmapper_t* mapper, ddjvu_rect_t* rect) nogil
	void ddjvu_unmap_point(ddjvu_rectmapper_t* mapper, int* x, int* y) nogil
	void ddjvu_unmap_rect(ddjvu_rectmapper_t* mapper, ddjvu_rect_t* rect) nogil

	cdef enum ddjvu_format_style_s:
		DDJVU_FORMAT_BGR24
		DDJVU_FORMAT_RGB24
		DDJVU_FORMAT_RGBMASK16
		DDJVU_FORMAT_RGBMASK32
		DDJVU_FORMAT_GREY8
		DDJVU_FORMAT_PALETTE8
		DDJVU_FORMAT_MSBTOLSB
		DDJVU_FORMAT_LSBTOMSB
	ctypedef int ddjvu_format_style_t
   
	ddjvu_format_t* ddjvu_format_create(ddjvu_format_style_t style, int nargs, unsigned int* args) nogil
	void ddjvu_format_set_row_order(ddjvu_format_t* format, int top_to_bottom) nogil
	void ddjvu_format_set_y_direction(ddjvu_format_t* format, int top_to_bottom) nogil
	void ddjvu_format_set_ditherbits(ddjvu_format_t* format, int bits) nogil
	void ddjvu_format_set_gamma(ddjvu_format_t* format, double gamma) nogil
	void ddjvu_format_release(ddjvu_format_t* format) nogil

	ddjvu_status_t ddjvu_thumbnail_status(ddjvu_document_t* document, int pagenum, int start) nogil

	cdef struct ddjvu_message_thumbnail_s:
		ddjvu_message_any_t any
		int pagenum

	int ddjvu_thumbnail_render(ddjvu_document_t* document, int pagenum, int* wptr, int* hptr, ddjvu_format_t* pixelformat, unsigned long rowsize, char* imagebuffer) nogil

	cdef struct ddjvu_message_progress_s:
		ddjvu_message_any_t any
		ddjvu_status_t status
		int percent

	ddjvu_job_t* ddjvu_document_print(ddjvu_document_t* document, FILE* output, int optc, char** optv) nogil
	ddjvu_job_t* ddjvu_document_save(ddjvu_document_t* document, FILE* output, int optc, char** optv) nogil

	void ddjvu_miniexp_release(ddjvu_document_t* document, cexpr_t expr) nogil

	cexpr_t ddjvu_document_get_outline(ddjvu_document_t* document) nogil
	cexpr_t ddjvu_document_get_anno(ddjvu_document_t* document, int compat) nogil
	cexpr_t ddjvu_document_get_pagetext(ddjvu_document_t* document, int pageno, char* maxdetail) nogil
	cexpr_t ddjvu_document_get_pageanno(ddjvu_document_t* document, int pageno) nogil
	char* ddjvu_anno_get_bgcolor(cexpr_t annotations) nogil
	char* ddjvu_anno_get_zoom(cexpr_t annotations) nogil
	char* ddjvu_anno_get_mode(cexpr_t annotations) nogil
	char* ddjvu_anno_get_horizalign(cexpr_t annotations) nogil
	char* ddjvu_anno_get_vertalign(cexpr_t annotations) nogil
	cexpr_t* ddjvu_anno_get_hyperlinks(cexpr_t annotations) nogil
	cexpr_t* ddjvu_anno_get_metadata_keys(cexpr_t annotations) nogil
	char* ddjvu_anno_get_metadata(cexpr_t annotations, cexpr_t key) nogil

	cdef union ddjvu_message_s:
		ddjvu_message_any_s m_any
		ddjvu_message_error_s m_error
		ddjvu_message_info_s m_info
		ddjvu_message_newstream_s m_newstream
		ddjvu_message_docinfo_s m_docinfo
		ddjvu_message_pageinfo_s m_pageinfo
		ddjvu_message_chunk_s m_chunk
		ddjvu_message_relayout_s m_relayout
		ddjvu_message_redisplay_s m_redisplay
		ddjvu_message_thumbnail_s m_thumbnail
		ddjvu_message_progress_s m_progress

cdef class Context

cdef class Document

cdef class DocumentExtension:
	cdef Document _document

cdef class DocumentPages(DocumentExtension):
	pass

cdef class DocumentFiles(DocumentExtension):
	pass

cdef class Document:
	cdef ddjvu_document_t* ddjvu_document
	cdef Context _context
	cdef DocumentPages _pages
	cdef DocumentFiles _files
	cdef object _queue
	cdef object _condition
	cdef object __weakref__
	cdef object __init(self, Context context, ddjvu_document_t* ddjvu_document)
	cdef object __clear(self)

cdef class _SexprWrapper:
	cdef object _document_weakref
	cdef cexpr_t _cexpr

cdef class DocumentOutline(DocumentExtension):
	cdef _SexprWrapper _sexpr
	cdef object _update_sexpr(self)

cdef class Annotations:
	cdef _SexprWrapper _sexpr
	cdef object _update_sexpr(self)
	cdef Document _document

cdef class DocumentAnnotations(Annotations):
	cdef int _compat

cdef class Hyperlinks:
	cdef object _sexpr

cdef class Metadata:
	cdef Annotations _annotations
	cdef object _keys

cdef class File:
	cdef int _n
	cdef int _have_info
	cdef ddjvu_fileinfo_t ddjvu_fileinfo
	cdef Document _document

cdef class Page:
	cdef Document _document
	cdef ddjvu_pageinfo_t ddjvu_pageinfo
	cdef int _have_info
	cdef int _n

cdef class PageAnnotations(Annotations):
	cdef Page _page

cdef class PageText:
	cdef Page _page
	cdef object _details
	cdef _SexprWrapper _sexpr
	cdef object _update_sexpr(self)

cdef class Context:
	cdef ddjvu_context_t* ddjvu_context
	cdef object _queue

cdef class PixelFormat:
	cdef ddjvu_format_t* ddjvu_format
	cdef int _bpp
	cdef int _dither_bpp
	cdef int _row_order
	cdef int _y_direction
	cdef double _gamma

cdef class PixelFormatRgb(PixelFormat):
	cdef int _rgb

cdef class PixelFormatRgbMask(PixelFormat):
	cdef unsigned int _params[4]
	
cdef class PixelFormatGrey(PixelFormat):
	pass

cdef class PixelFormatPalette(PixelFormat):
	cdef unsigned int _palette[216]

cdef class PixelFormatPackedBits(PixelFormat):
	cdef int _little_endian
	pass

cdef class Job:
	cdef Context _context
	cdef ddjvu_job_t* ddjvu_job
	cdef object _queue
	cdef object _condition
	cdef object __init(self, Context context, ddjvu_job_t *ddjvu_job)
	cdef object __clear(self)
	cdef object __weakref__

cdef class PageJob(Job):
	pass

cdef class SaveJob(Job):
	cdef object _file

cdef class DocumentDecodingJob(Job):
	cdef object _document
	cdef object __init_ddj(self, Document document)

cdef class AffineTransform:
	cdef ddjvu_rectmapper_t* ddjvu_rectmapper

cdef class Message:
	cdef ddjvu_message_t* ddjvu_message
	cdef Context _context
	cdef Document _document
	cdef PageJob _page_job
	cdef Job _job
	cdef object __init(self)

cdef class ErrorMessage(Message):
	cdef object _message
	cdef object _location

cdef class InfoMessage(Message):
	cdef object _message

cdef class Stream:
	cdef int _streamid
	cdef int _open
	cdef Document _document

cdef class NewStreamMessage(Message):
	cdef object _name
	cdef object _uri
	cdef Stream _stream

cdef class DocInfoMessage(Message):
	pass

cdef class PageInfoMessage(Message):
	pass

cdef class ChunkMessage(Message):
	pass

cdef class RelayoutMessage(ChunkMessage):
	pass

cdef class RedisplayMessage(ChunkMessage):
	pass

cdef class ThumbnailMessage(Message):
	cdef int _page_no

cdef class ProgressMessage(Message):
	cdef int _percent
	cdef ddjvu_status_t _status

cdef class Thumbnail:
	cdef Page _page

# vim:ts=4 sw=4 noet ft=pyrex
