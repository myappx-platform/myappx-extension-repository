package org.idempiere.myappx.extension.repository;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;

import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.WriteListener;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpServletResponseWrapper;

/**
 * Rewrites {@code __MYAPPX_CATALOG_BASE__} in catalog JSON to the host that
 * requested the file, and marks catalog responses as revalidated.
 * <p>
 * Extension Management fetches the catalog with {@code IDEMPIERE_EXTENSION_REPOSITORY}
 * and then uses absolute {@code metadataUrl} / {@code downloadUrl} values as-is.
 * Catalog versions stay at {@code 14.0.0} / {@code 1.0.0} across SNAPSHOT rebuilds,
 * so the same URL can change bytes; responses are {@code no-cache}.
 * <p>
 * The placeholder string must match {@code CATALOG_BASE_PLACEHOLDER} in
 * {@code scripts/cataloglib.py}.
 */
public class CatalogBaseUrlFilter implements Filter {

	static final String PLACEHOLDER = "__MYAPPX_CATALOG_BASE__";

	@Override
	public void init(FilterConfig filterConfig) {
	}

	@Override
	public void doFilter(javax.servlet.ServletRequest request, javax.servlet.ServletResponse response, FilterChain chain)
			throws IOException, ServletException {
		HttpServletRequest httpRequest = (HttpServletRequest) request;
		HttpServletResponse httpResponse = (HttpServletResponse) response;
		httpResponse.setHeader("Cache-Control", "no-cache");

		String uri = httpRequest.getRequestURI();
		if (uri == null || !uri.endsWith(".json")) {
			chain.doFilter(request, response);
			return;
		}

		CapturingResponse capture = new CapturingResponse(httpResponse);
		chain.doFilter(request, capture);
		capture.finish();
		if (capture.suppressBody() || httpResponse.isCommitted()) {
			return;
		}

		byte[] body = capture.body();
		String text = new String(body, StandardCharsets.UTF_8);
		if (text.contains(PLACEHOLDER)) {
			text = text.replace(PLACEHOLDER, requestBase(httpRequest));
			body = text.getBytes(StandardCharsets.UTF_8);
			httpResponse.setContentType("application/json;charset=UTF-8");
		}
		httpResponse.setContentLength(body.length);
		httpResponse.getOutputStream().write(body);
	}

	@Override
	public void destroy() {
	}

	/**
	 * Base URL without a trailing slash: scheme, host, port, and context path.
	 * {@code X-Forwarded-Proto} / {@code X-Forwarded-Host} are used when a proxy set them
	 * on this request. Each response is rewritten for its own caller.
	 */
	static String requestBase(HttpServletRequest request) {
		String forwardedHost = firstHeaderValue(request.getHeader("X-Forwarded-Host"));
		if (forwardedHost != null) {
			String proto = firstHeaderValue(request.getHeader("X-Forwarded-Proto"));
			if (proto == null || proto.isEmpty()) {
				proto = request.getScheme();
			}
			return proto + "://" + forwardedHost + request.getContextPath();
		}
		StringBuffer url = request.getRequestURL();
		String requestUri = request.getRequestURI();
		String origin = url.substring(0, url.length() - requestUri.length());
		return origin + request.getContextPath();
	}

	private static String firstHeaderValue(String header) {
		if (header == null) {
			return null;
		}
		String value = header.split(",")[0].trim();
		return value.isEmpty() ? null : value;
	}

	private static final class CapturingResponse extends HttpServletResponseWrapper {
		private final ByteArrayOutputStream buffer = new ByteArrayOutputStream();
		private ServletOutputStream outputStream;
		private PrintWriter writer;
		private boolean suppressBody;
		private int status = SC_OK;

		private CapturingResponse(HttpServletResponse response) {
			super(response);
		}

		private byte[] body() {
			return buffer.toByteArray();
		}

		private boolean suppressBody() {
			return suppressBody || status == SC_NOT_MODIFIED || status == SC_NO_CONTENT || status >= 400;
		}

		private void finish() throws IOException {
			if (writer != null) {
				writer.flush();
			} else if (outputStream != null) {
				outputStream.flush();
			}
		}

		@Override
		public void setStatus(int sc) {
			status = sc;
			super.setStatus(sc);
		}

		@Override
		public void sendError(int sc) throws IOException {
			status = sc;
			suppressBody = true;
			super.sendError(sc);
		}

		@Override
		public void sendError(int sc, String msg) throws IOException {
			status = sc;
			suppressBody = true;
			super.sendError(sc, msg);
		}

		@Override
		public void setContentLength(int len) {
		}

		@Override
		public void setContentLengthLong(long len) {
		}

		@Override
		public void setHeader(String name, String value) {
			if (!isContentLength(name)) {
				super.setHeader(name, value);
			}
		}

		@Override
		public void addHeader(String name, String value) {
			if (!isContentLength(name)) {
				super.addHeader(name, value);
			}
		}

		@Override
		public void setIntHeader(String name, int value) {
			if (!isContentLength(name)) {
				super.setIntHeader(name, value);
			}
		}

		@Override
		public ServletOutputStream getOutputStream() {
			if (outputStream == null) {
				outputStream = new ServletOutputStream() {
					@Override
					public void write(int b) {
						buffer.write(b);
					}

					@Override
					public boolean isReady() {
						return true;
					}

					@Override
					public void setWriteListener(WriteListener writeListener) {
					}
				};
			}
			return outputStream;
		}

		@Override
		public PrintWriter getWriter() {
			if (writer == null) {
				writer = new PrintWriter(new OutputStreamWriter(getOutputStream(), StandardCharsets.UTF_8), false);
			}
			return writer;
		}

		@Override
		public void flushBuffer() {
		}

		private static boolean isContentLength(String name) {
			return "Content-Length".equalsIgnoreCase(name);
		}
	}
}
