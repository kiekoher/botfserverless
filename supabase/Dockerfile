# Use an official Deno image as a parent image
FROM denoland/deno:1.37.1

# Install Supabase CLI
RUN deno run --allow-all --unsafe https://deno.land/x/deno_info/main.ts && \
    deno install --allow-all --no-check -r -f https://deno.land/x/supabase/cli.ts

# Set the working directory
WORKDIR /app
