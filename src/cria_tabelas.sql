CREATE TABLE leilao (
	codigo_artigo	 VARCHAR(512) UNIQUE NOT NULL,
	titulo		 VARCHAR(40) NOT NULL,
	data_hora_fim	 TIMESTAMP NOT NULL,
	detalhes_adicionais VARCHAR(512) DEFAULT Null,
	preco_minimo	 FLOAT(8) NOT NULL,
	encerrado		 BOOL NOT NULL DEFAULT False,
	descricao_atual	 VARCHAR(512) NOT NULL,
	licitacao_atual	 BIGINT,
	vencedor		 VARCHAR(512),
	utilizador_username VARCHAR(20) NOT NULL,
	PRIMARY KEY(codigo_artigo)
);

CREATE TABLE utilizador (
	username	 VARCHAR(20) UNIQUE NOT NULL,
	email	 VARCHAR(512) UNIQUE NOT NULL,
	password	 VARCHAR(20) NOT NULL,
	token	 VARCHAR(512),
	administrador BOOL NOT NULL,
	banido	 BOOL NOT NULL,
	PRIMARY KEY(username)
);

CREATE TABLE mensagens_leilao (
	mensagens		 VARCHAR(512) NOT NULL,
	data_mensagem	 TIMESTAMP NOT NULL,
	id			 BIGINT NOT NULL,
	utilizador_username	 VARCHAR(20) NOT NULL,
	leilao_codigo_artigo VARCHAR(512) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE mensagens_utilizador (
	mensagens		 VARCHAR(512) NOT NULL,
	data_mensagem	 TIMESTAMP NOT NULL,
	lido		 BOOL NOT NULL,
	id			 BIGINT,
	remetente		 VARCHAR(512) NOT NULL,
	leilao_codigo_artigo VARCHAR(512) NOT NULL,
	utilizador_username	 VARCHAR(20) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE licitacao (
	id			 BIGINT,
	valor		 FLOAT(8) NOT NULL,
	data		 TIMESTAMP NOT NULL,
	valida		 BOOL NOT NULL,
	utilizador_username	 VARCHAR(20) NOT NULL,
	leilao_codigo_artigo VARCHAR(512) NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE historico (
	descricao		 VARCHAR(512) NOT NULL,
	data		 TIMESTAMP NOT NULL,
	titulo		 VARCHAR(512) NOT NULL,
	detalhes_adicionais	 VARCHAR(512) NOT NULL,
	id			 BIGINT,
	leilao_codigo_artigo VARCHAR(512) NOT NULL,
	PRIMARY KEY(id)
);

ALTER TABLE leilao ADD CONSTRAINT leilao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE mensagens_leilao ADD CONSTRAINT mensagens_leilao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE mensagens_leilao ADD CONSTRAINT mensagens_leilao_fk2 FOREIGN KEY (leilao_codigo_artigo) REFERENCES leilao(codigo_artigo);
ALTER TABLE mensagens_utilizador ADD CONSTRAINT mensagens_utilizador_fk1 FOREIGN KEY (leilao_codigo_artigo) REFERENCES leilao(codigo_artigo);
ALTER TABLE mensagens_utilizador ADD CONSTRAINT mensagens_utilizador_fk2 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk1 FOREIGN KEY (utilizador_username) REFERENCES utilizador(username);
ALTER TABLE licitacao ADD CONSTRAINT licitacao_fk2 FOREIGN KEY (leilao_codigo_artigo) REFERENCES leilao(codigo_artigo);
ALTER TABLE historico ADD CONSTRAINT historico_fk1 FOREIGN KEY (leilao_codigo_artigo) REFERENCES leilao(codigo_artigo);

