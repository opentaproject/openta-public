ARG FULL_VERSION=multi

# Stage 1: start from the private full image and remove all Git artifacts
FROM opentaproject/openta-full:${FULL_VERSION} AS cleaned
USER root
RUN set -eux; \
    # Remove all .git directories everywhere (avoid special FS paths)
    find / -path /proc -prune -o -path /sys -prune -o -path /dev -prune -o \
         -type d -name .git -exec rm -rf {} +; \
    # Remove Git-related files
    find / -path /proc -prune -o -path /sys -prune -o -path /dev -prune -o \
         -type f \( -name '.gitignore' -o -name '.gitattributes' -o -name '.gitmodules' -o -name '.gitkeep' \) -exec rm -f {} +; \
    # Preserve old-install explicit removals inside /srv
    rm -rf \
      /srv/frontend \
      /srv/openta/presentation; \
    rm -rf /srv/openta/docker* || true; \
    rm -rf /srv/openta/django/backend/db_* || true; \
    rm -rf /srv/openta/django/backend/install* || true; \
    rm -rf /srv/openta/django/backend/osx* || true

# Stage 2: create a new image that contains only the cleaned filesystem
FROM scratch
COPY --from=cleaned / /
EXPOSE 8000
