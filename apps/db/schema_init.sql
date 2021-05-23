--
-- PostgreSQL database dump
--

-- Dumped from database version 13.3
-- Dumped by pg_dump version 13.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: entries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.entries (
    id integer NOT NULL,
    unit character varying(25) NOT NULL,
    datetime timestamp without time zone NOT NULL,
    opening numeric NOT NULL,
    closing numeric NOT NULL,
    interpolated boolean NOT NULL
);


ALTER TABLE public.entries OWNER TO postgres;

--
-- Name: entries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.entries ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.entries_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: rolling_returns; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rolling_returns (
    rid integer NOT NULL,
    date date NOT NULL,
    opening numeric NOT NULL,
    closing numeric NOT NULL,
    unit character varying(25) NOT NULL
);


ALTER TABLE public.rolling_returns OWNER TO postgres;

--
-- Name: rolling_returns_rid_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.rolling_returns ALTER COLUMN rid ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.rolling_returns_rid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: entries entries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.entries
    ADD CONSTRAINT entries_pkey PRIMARY KEY (id);


--
-- Name: rolling_returns rolling_returns_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rolling_returns
    ADD CONSTRAINT rolling_returns_pkey PRIMARY KEY (rid);


--
-- PostgreSQL database dump complete
--

