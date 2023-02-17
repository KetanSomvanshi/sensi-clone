-- init script to initialize the database table
-- this is to be used by docker postgres container

create TABLE public.sensi_underlying (
	id serial4 NOT NULL,
	created_at timestamptz NOT NULL,
	updated_at timestamptz NOT NULL DEFAULT now(),
	is_deleted bool NOT NULL DEFAULT false,
	symbol varchar(1000) NULL,
	underlying varchar(1000) NULL,
	"token" varchar(1000) NOT NULL,
	instrument_type varchar(10) NULL,
	expiry timestamptz NULL,
	strike float8 NULL,
	CONSTRAINT sensi_underlying_pk PRIMARY KEY (id)
);
create index sensi_underlying_symbol_idx on public.sensi_underlying USING btree (symbol);
create index sensi_underlying_token_idx on public.sensi_underlying USING btree (token);


create TABLE public.sensi_derivative (
	id serial4 NOT NULL,
	created_at timestamptz NOT NULL,
	updated_at timestamptz NOT NULL DEFAULT now(),
	is_deleted bool NOT NULL DEFAULT false,
	symbol varchar(1000) NULL,
	underlying varchar(1000) NULL,
	"token" varchar(1000) NOT NULL,
	instrument_type varchar(10) NULL,
	expiry timestamptz NULL,
	strike float8 NULL,
	underlying_id int4 NULL,
	CONSTRAINT sensi_derivatives_pk PRIMARY KEY (id)
);
create index sensi_derivatives_token_idx on public.sensi_derivative USING btree (token);
create index sensi_derivatives_underlying_id_idx on public.sensi_derivative USING btree (underlying_id);
alter table public.sensi_derivative add CONSTRAINT sensi_derivatives_fk FOREIGN KEY (underlying_id) REFERENCES public.sensi_underlying(id);