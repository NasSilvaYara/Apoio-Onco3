-- Esquema do banco ApoioOnco (SQLite) gerado a partir das migrações do Django.
-- Para recriar:  python manage.py migrate     (este arquivo é só referência/documentação)

BEGIN;
--
-- Create model TipoApoio
--
CREATE TABLE "ongs_tipoapoio" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "nome" varchar(60) NOT NULL UNIQUE, "descricao" varchar(200) NOT NULL, "ativo" bool NOT NULL);
--
-- Create model ConteudoInformativo
--
CREATE TABLE "ongs_conteudoinformativo" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "categoria" varchar(20) NOT NULL, "titulo" varchar(200) NOT NULL, "slug" varchar(220) NOT NULL UNIQUE, "resumo" varchar(250) NOT NULL, "corpo" text NOT NULL, "publicado" bool NOT NULL, "criado_em" datetime NOT NULL, "atualizado_em" datetime NOT NULL, "autor_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model Instituicao
--
CREATE TABLE "ongs_instituicao" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "cnpj" varchar(14) NOT NULL UNIQUE, "nome" varchar(200) NOT NULL, "tipo" varchar(20) NOT NULL, "descricao" varchar(300) NOT NULL, "horario_atendimento" text NOT NULL, "logo" varchar(100) NOT NULL, "cep" varchar(9) NOT NULL, "logradouro" varchar(250) NOT NULL, "numero" varchar(20) NOT NULL, "complemento" varchar(100) NOT NULL, "bairro" varchar(100) NOT NULL, "cidade" varchar(100) NOT NULL, "estado" varchar(2) NOT NULL, "telefone" varchar(15) NOT NULL, "whatsapp" varchar(15) NOT NULL, "email_contato" varchar(254) NOT NULL, "site" varchar(200) NOT NULL, "redes_sociais" varchar(200) NOT NULL, "status" varchar(10) NOT NULL, "motivo_rejeicao" text NOT NULL, "avaliado_em" datetime NULL, "criado_em" datetime NOT NULL, "atualizado_em" datetime NOT NULL, "avaliado_por_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "usuario_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE "ongs_instituicao_servicos" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "instituicao_id" integer NOT NULL REFERENCES "ongs_instituicao" ("id") DEFERRABLE INITIALLY DEFERRED, "tipoapoio_id" integer NOT NULL REFERENCES "ongs_tipoapoio" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "ongs_conteudoinformativo_autor_id_8875201e" ON "ongs_conteudoinformativo" ("autor_id");
CREATE INDEX "ongs_instituicao_avaliado_por_id_10cc5c71" ON "ongs_instituicao" ("avaliado_por_id");
CREATE INDEX "inst_busca_idx" ON "ongs_instituicao" ("status", "estado", "cidade");
CREATE UNIQUE INDEX "ongs_instituicao_servicos_instituicao_id_tipoapoio_id_f3f83615_uniq" ON "ongs_instituicao_servicos" ("instituicao_id", "tipoapoio_id");
CREATE INDEX "ongs_instituicao_servicos_instituicao_id_9a00964d" ON "ongs_instituicao_servicos" ("instituicao_id");
CREATE INDEX "ongs_instituicao_servicos_tipoapoio_id_69daed8d" ON "ongs_instituicao_servicos" ("tipoapoio_id");
COMMIT;
