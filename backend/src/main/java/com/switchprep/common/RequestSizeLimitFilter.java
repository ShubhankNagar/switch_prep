package com.switchprep.common;

import com.switchprep.config.AppProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ReadListener;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletInputStream;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletRequestWrapper;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Rejects request bodies larger than {@code app.limits.max-request-bytes}. Spring has no built-in cap for JSON
 * bodies, and a small server must not buffer whatever a client chooses to send.
 */
@Component
public class RequestSizeLimitFilter extends OncePerRequestFilter {

    private final long maxBytes;

    public RequestSizeLimitFilter(AppProperties props) {
        this.maxBytes = props.limits().maxRequestBytes();
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        long declared = request.getContentLengthLong();
        if (declared > maxBytes) {
            response.setStatus(HttpStatus.PAYLOAD_TOO_LARGE.value());
            response.setContentType(MediaType.APPLICATION_JSON_VALUE);
            response.getWriter().write("{\"error\":\"Request is too large\"}");
            return;
        }
        // no Content-Length (chunked upload): count the bytes as they are read
        chain.doFilter(declared < 0 ? new LimitedRequest(request, maxBytes) : request, response);
    }

    private static final class LimitedRequest extends HttpServletRequestWrapper {

        private final long maxBytes;

        LimitedRequest(HttpServletRequest request, long maxBytes) {
            super(request);
            this.maxBytes = maxBytes;
        }

        @Override
        public ServletInputStream getInputStream() throws IOException {
            ServletInputStream in = super.getInputStream();
            return new ServletInputStream() {
                private long count;

                @Override
                public int read() throws IOException {
                    int b = in.read();
                    if (b >= 0 && ++count > maxBytes) throw new IOException("Request is too large");
                    return b;
                }

                @Override
                public int read(byte[] buffer, int off, int len) throws IOException {
                    int n = in.read(buffer, off, len);
                    if (n > 0 && (count += n) > maxBytes) throw new IOException("Request is too large");
                    return n;
                }

                @Override
                public boolean isFinished() { return in.isFinished(); }

                @Override
                public boolean isReady() { return in.isReady(); }

                @Override
                public void setReadListener(ReadListener listener) { in.setReadListener(listener); }
            };
        }
    }
}
