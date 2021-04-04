FROM docker.io/library/python:3.8 as build-env

# Set pip to have cleaner logs and no saved cache
ENV PIP_NO_CACHE_DIR=false \
    PIPENV_HIDE_EMOJIS=1 \
    PIPENV_IGNORE_VIRTUALENVS=1 \
    PIPENV_NOSPIN=1

# Install pipenv
RUN pip install -U pipenv

# Create the working directory
WORKDIR /app

# Copy Pipfiles
COPY Pipfile* ./

# Install project dependencies
RUN pipenv install --dev --deploy

# Copy project files into working directory
# This is done last to prevent unnecessary image rebuilds
COPY . .

# Build pex file
RUN pipenv run shiv-build


FROM docker.io/library/python:3.8-slim

LABEL org.opencontainers.image.source https://github.com/weeb-poly/syncplay-proxy

# Create the working directory
WORKDIR /app

# Copy pex file from build-env
COPY --from=build-env /app/syncplay.pyz /app/

CMD ["./syncplay.pyz"]
