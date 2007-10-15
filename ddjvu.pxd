# Copyright (c) 2007 Jakub Wilk <ubanus@users.sf.net>

cdef extern from 'stdio.h':
	struct _IO_FILE
	ctypedef _IO_FILE FILE

from miniexp cimport cexp_t

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

	ddjvu_context_t* ddjvu_context_create(char* program_name)
	void ddjvu_context_release(ddjvu_context_t* context)

	void ddjvu_cache_set_size(ddjvu_context_t* context, unsigned long cachesize)
	unsigned long ddjvu_cache_get_size(ddjvu_context_t* context)
	void ddjvu_cache_clear(ddjvu_context_t* context)
	
	ddjvu_message_t* ddjvu_message_peek(ddjvu_context_t* context)
	ddjvu_message_t* ddjvu_message_wait(ddjvu_context_t* context)
	void ddjvu_message_pop(ddjvu_context_t* context)

	ctypedef void (*ddjvu_message_callback_t)(ddjvu_context_t* context, void* closure)

	void ddjvu_message_set_callback(ddjvu_context_t* context, ddjvu_message_callback_t callback, void* closure)

	cdef enum ddjvu_status_e:
		DDJVU_JOB_NOTSTARTED
		DDJVU_JOB_STARTED
		DDJVU_JOB_OK
		DDJVU_JOB_FAILED
		DDJVU_JOB_STOPPED
	ctypedef ddjvu_status_e ddjvu_status_t

	ddjvu_status_t ddjvu_job_status(ddjvu_job_t* job)
	int ddjvu_job_done(ddjvu_job_t* job)
	int ddjvu_job_error(ddjvu_job_t* job)
	void ddjvu_job_stop(ddjvu_job_t* job)
	void ddjvu_job_set_user_data(ddjvu_job_t* job, void* userdata)
	void* ddjvu_job_get_user_data(ddjvu_job_t* job)
	void ddjvu_job_release(ddjvu_job_t* job)

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

	ddjvu_document_t* ddjvu_document_create(ddjvu_context_t* context, char* url, int cache)
	ddjvu_document_t* ddjvu_document_create_by_filename(ddjvu_context_t* context, char* filename, int cache)
	ddjvu_job_t* ddjvu_document_job(ddjvu_document_t* document)
	void ddjvu_document_release(ddjvu_document_t* document)

	void ddjvu_document_set_user_data(ddjvu_document_t* document, void* userdata)
	void* ddjvu_document_get_user_data(ddjvu_document_t* document)

	ddjvu_status_t ddjvu_document_decoding_status(ddjvu_document_t* document)
	int ddjvu_document_decoding_done(ddjvu_document_t* document)
	int ddjvu_document_decoding_error(ddjvu_document_t* document)

	cdef struct ddjvu_message_newstream_s:
		ddjvu_message_any_t any
		int streamid
		char* name
		char* url

	void ddjvu_stream_write(ddjvu_document_t* document, int streamid, char* data, unsigned long datalen)
	void ddjvu_stream_close(ddjvu_document_t* document, int streamid, int stop)

	cdef struct ddjvu_message_docinfo_s:
		ddjvu_message_any_t any

	cdef enum ddjvu_document_type_t:
		DDJVU_DOCTYPE_UNKNOWN
		DDJVU_DOCTYPE_SINGLEPAGE
		DDJVU_DOCTYPE_BUNDLED
		DDJVU_DOCTYPE_INDIRECT
		DDJVU_DOCTYPE_OLD_BUNDLED
		DDJVU_DOCTYPE_OLD_INDEXED

	ddjvu_document_type_t ddjvu_document_get_type(ddjvu_document_t* document)
	int ddjvu_document_get_pagenum(ddjvu_document_t* document)
	int ddjvu_document_get_filenum(ddjvu_document_t* document)

	cdef struct ddjvu_fileinfo_s:
		char type
		int pageno
		int size
		char* id
		char* name
		char* title
	ctypedef ddjvu_fileinfo_s ddjvu_fileinfo_t

	ddjvu_status_t ddjvu_document_get_fileinfo(ddjvu_document_t* document, int fileno, ddjvu_fileinfo_t* info)
	int ddjvu_document_check_pagedata(ddjvu_document_t* document, int pageno)

	cdef struct ddjvu_pageinfo_s:
		int width
		int height
		int dpi
		int rotation
		int version
	ctypedef ddjvu_pageinfo_s ddjvu_pageinfo_t

	ddjvu_status_t ddjvu_document_get_pageinfo(ddjvu_document_t* document, int pageno, ddjvu_pageinfo_t* info)
	ddjvu_status_t ddjvu_document_get_pageinfo_imp(ddjvu_document_t* document, int pageno, ddjvu_pageinfo_t* info, unsigned int infosz)
	char* ddjvu_document_get_pagedump(ddjvu_document_t* document, int pageno)
	char* ddjvu_document_get_filedump(ddjvu_document_t* document, int fileno)

	ddjvu_page_t* ddjvu_page_create_by_pageno(ddjvu_document_t* document, int pageno)
	ddjvu_page_t* ddjvu_page_create_by_pageid(ddjvu_document_t* document, char* pageid)
	ddjvu_job_t* ddjvu_page_job(ddjvu_page_t* page)

	void ddjvu_page_release(ddjvu_page_t* page)
	void ddjvu_page_set_user_data(ddjvu_page_t* page, void* userdata)
	void* ddjvu_page_get_user_data(ddjvu_page_t* page)

	ddjvu_status_t ddjvu_page_decoding_status(ddjvu_page_t* page)
	int ddjvu_page_decoding_done(ddjvu_page_t* page)
	int ddjvu_page_decoding_error(ddjvu_page_t* page)

	cdef struct ddjvu_message_pageinfo_s:
		ddjvu_message_any_t any

	cdef struct ddjvu_message_relayout_s:
		ddjvu_message_any_t any

	cdef struct ddjvu_message_redisplay_s:
		ddjvu_message_any_t any

	cdef struct ddjvu_message_chunk_s:
		ddjvu_message_any_t any
	char* chunkid

	int ddjvu_page_get_width(ddjvu_page_t* page)
	int ddjvu_page_get_height(ddjvu_page_t* page)
	int ddjvu_page_get_resolution(ddjvu_page_t* page)
	double ddjvu_page_get_gamma(ddjvu_page_t* page)
	int ddjvu_page_get_version(ddjvu_page_t* page)
	int ddjvu_code_get_version()

	cdef enum ddjvu_page_type_t:
		DDJVU_PAGETYPE_UNKNOWN
		DDJVU_PAGETYPE_BITONAL
		DDJVU_PAGETYPE_PHOTO
		DDJVU_PAGETYPE_COMPOUND

	ddjvu_page_type_t ddjvu_page_get_type(ddjvu_page_t* page)

	cdef enum ddjvu_page_rotation_t:
		DDJVU_ROTATE_0
		DDJVU_ROTATE_90
		DDJVU_ROTATE_180
		DDJVU_ROTATE_270

	void ddjvu_page_set_rotation(ddjvu_page_t* page, ddjvu_page_rotation_t rot)
	ddjvu_page_rotation_t ddjvu_page_get_rotation(ddjvu_page_t* page)
	ddjvu_page_rotation_t ddjvu_page_get_initial_rotation(ddjvu_page_t* page)

	cdef enum ddjvu_render_mode_t:
		DDJVU_RENDER_COLOR
		DDJVU_RENDER_BLACK
		DDJVU_RENDER_COLORONLY
		DDJVU_RENDER_MASKONLY
		DDJVU_RENDER_BACKGROUND
		DDJVU_RENDER_FOREGROUND

	cdef struct ddjvu_rect_s:
		int x, y
		unsigned int w, h

	int ddjvu_page_render(ddjvu_page_t* page, ddjvu_render_mode_t mode, ddjvu_rect_t* pagerect, ddjvu_rect_t* renderrect, ddjvu_format_t* pixelformat, unsigned long rowsize, char* imagebuffer)

	ddjvu_rectmapper_t* ddjvu_rectmapper_create(ddjvu_rect_t* input, ddjvu_rect_t* output)
	void ddjvu_rectmapper_modify(ddjvu_rectmapper_t* mapper, int rotation, int mirrorx, int mirrory)
	void ddjvu_rectmapper_release(ddjvu_rectmapper_t* mapper)
	void ddjvu_map_point(ddjvu_rectmapper_t* mapper, int* x, int* y)
	void ddjvu_map_rect(ddjvu_rectmapper_t* mapper, ddjvu_rect_t* rect)
	void ddjvu_unmap_point(ddjvu_rectmapper_t* mapper, int* x, int* y)
	void ddjvu_unmap_rect(ddjvu_rectmapper_t* mapper, ddjvu_rect_t* rect)

	cdef enum ddjvu_format_style_t:
		DDJVU_FORMAT_BGR24
		DDJVU_FORMAT_RGB24
		DDJVU_FORMAT_RGBMASK16
		DDJVU_FORMAT_RGBMASK32
		DDJVU_FORMAT_GREY8
		DDJVU_FORMAT_PALETTE8
		DDJVU_FORMAT_MSBTOLSB
		DDJVU_FORMAT_LSBTOMSB
   
	ddjvu_format_t* ddjvu_format_create(ddjvu_format_style_t style, int nargs, unsigned int* args)
	void ddjvu_format_set_row_order(ddjvu_format_t* format, int top_to_bottom)
	void ddjvu_format_set_y_direction(ddjvu_format_t* format, int top_to_bottom)
	void ddjvu_format_set_ditherbits(ddjvu_format_t* format, int bits)
	void ddjvu_format_set_gamma(ddjvu_format_t* format, double gamma)
	void ddjvu_format_release(ddjvu_format_t* format)

	ddjvu_status_t ddjvu_thumbnail_status(ddjvu_document_t* document, int pagenum, int start)

	cdef struct ddjvu_message_thumbnail_s:
		ddjvu_message_any_t any
		int pagenum

	int ddjvu_thumbnail_render(ddjvu_document_t* document, int pagenum, int* wptr, int* hptr, ddjvu_format_t* pixelformat, unsigned long rowsize, char* imagebuffer)

	cdef struct ddjvu_message_progress_s:
		ddjvu_message_any_t any
		ddjvu_status_t status
		int percent

	ddjvu_job_t* ddjvu_document_print(ddjvu_document_t* document, FILE* output, int optc, char** optv)
	ddjvu_job_t* ddjvu_document_save(ddjvu_document_t* document, FILE* output, int optc, char** optv)

	void ddjvu_miniexp_release(ddjvu_document_t* document, cexp_t expr)

	cexp_t ddjvu_document_get_outline(ddjvu_document_t* document)
	cexp_t ddjvu_document_get_anno(ddjvu_document_t* document, int compat)
	cexp_t ddjvu_document_get_pagetext(ddjvu_document_t* document, int pageno, char* maxdetail)
	cexp_t ddjvu_document_get_pageanno(ddjvu_document_t* document, int pageno)
	char* ddjvu_anno_get_bgcolor(cexp_t annotations)
	char* ddjvu_anno_get_zoom(cexp_t annotations)
	char* ddjvu_anno_get_mode(cexp_t annotations)
	char* ddjvu_anno_get_horizalign(cexp_t annotations)
	char* ddjvu_anno_get_vertalign(cexp_t annotations)
	cexp_t* ddjvu_anno_get_hyperlinks(cexp_t annotations)
	cexp_t* ddjvu_anno_get_metadata_keys(cexp_t annotations)
	char* ddjvu_anno_get_metadata(cexp_t annotations, cexp_t key)

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



cdef class DocumentExtension:
	cdef object _document_weakref

cdef class DocumentPages(DocumentExtension):
	pass

cdef class DocumentFiles(DocumentExtension):
	pass

cdef class Document:
	cdef ddjvu_document_t* ddjvu_document
	cdef DocumentPages _pages
	cdef DocumentFiles _files
	cdef object __weakref__

cdef class File:
	cdef int _n
	cdef Document _document

cdef class Page:
	cdef int _n
	cdef Document _document

cdef class FileInfo:
	cdef ddjvu_fileinfo_t ddjvu_fileinfo
	cdef Document _document

cdef class PageInfo:
	cdef ddjvu_pageinfo_t ddjvu_pageinfo
	cdef Document _document

cdef class Context:
	cdef ddjvu_context_t* ddjvu_context

cdef class PageJob:
	cdef ddjvu_page_t* ddjvu_page

cdef class Job:
	cdef ddjvu_job_t* ddjvu_job

cdef class Message:
	cdef ddjvu_message_t* ddjvu_message
	cdef Context _context
	cdef Document _document
	cdef PageJob _page_job
	cdef Job _job

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

cdef class RelayoutMessage(Message):
	pass

cdef class RedisplayMessage(Message):
	pass

cdef class ChunkMessage(Message):
	pass

cdef class ThumbnailMessage(Message):
	pass

cdef class ProgressMessage(Message):
	pass

# vim:ts=4 sw=4 noet
