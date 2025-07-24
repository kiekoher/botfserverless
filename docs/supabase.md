# Configuración de Supabase

Antes de crear las tablas es necesario habilitar la extensión para vectores. Abre el **SQL editor** en el panel de Supabase y ejecuta:

```sql
create extension if not exists vector;
```

Luego crea las tablas que almacenarán los documentos, sus embeddings y el historial de conversaciones. A continuación se muestra un ejemplo básico:

```sql
create table documents (
  id bigint generated always as identity primary key,
  file_name text not null,
  content text
);

create table chunks (
  id bigint generated always as identity primary key,
  document_id bigint references documents(id),
  content_text text,
  embedding vector(1536)
);

create table knowledge_base (
  id bigint generated always as identity primary key,
  source_file text,
  content_type text,
  data jsonb
);

create table embeddings (
  id bigint generated always as identity primary key,
  knowledge_id bigint references knowledge_base(id),
  embedding vector(1536),
  content_text text
);

create table conversations (
  id bigint generated always as identity primary key,
  user_id text,
  user_message text,
  bot_response text,
  context_chunks jsonb,
  created_at timestamp with time zone default now()
);
```
