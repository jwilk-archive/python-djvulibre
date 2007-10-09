# Copyright (c) 2007 Jakub Wilk <ubanus@users.sf.net>

cdef extern from "libdjvu/ddjvuapi.h":
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
	
# vim:ts=4 sw=4 noet
