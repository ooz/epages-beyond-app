FROM python:3-slim

LABEL maintainer="oliverzscheyge@gmail.com"

# Prevent apt from querying for a keyboard configuration
ENV DEBIAN_FRONTEND noninteractive

# Dependencies to render PDFs
RUN apt-get update && apt-get install -y --no-install-recommends \
		wkhtmltopdf \
    xauth \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Using a "virtual" X server to run wkhtmltopdf:
# https://github.com/JazzCore/python-pdfkit/wiki/Using-wkhtmltopdf-without-X-server
RUN echo '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf -q $*' > /usr/bin/wkhtmltopdf.sh
RUN chmod a+x /usr/bin/wkhtmltopdf.sh
RUN ln -s /usr/bin/wkhtmltopdf.sh /usr/local/bin/wkhtmltopdf
RUN ln -s /usr/bin/wkhtmltopdf.sh ./bin/wkhtmltopdf

RUN pip install pipenv

# Copy order app files
COPY static /static
COPY templates /templates
COPY *.py /
COPY Pipfile* /

# Install dependencies
RUN pipenv install

# Run app
CMD pipenv run python /app.py
