# Use the official Odoo 16 image as the base image
FROM odoo:17

# Update package lists and install nano
USER root
RUN apt-get update && \
    apt-get install -y nano && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Switch back to the Odoo user
USER odoo

# Set the entrypoint for the container
CMD ["odoo"]
