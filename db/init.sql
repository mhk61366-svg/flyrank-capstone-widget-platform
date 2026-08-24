CREATE TABLE widgets (
    id            uuid PRIMARY KEY,
    tenant_id     uuid NOT NULL,
    type          text NOT NULL DEFAULT 'signup_form',
    title         text NOT NULL,
    description   text,
    button_text   text NOT NULL DEFAULT 'Submit',
    is_active     boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_widgets_tenant_id ON widgets (tenant_id);

CREATE TABLE submissions (
    id                  uuid PRIMARY KEY,
    widget_id           uuid NOT NULL REFERENCES widgets(id),
    tenant_id           uuid NOT NULL,
    name                text NOT NULL,
    email               text NOT NULL,
    age                 int NOT NULL,
    gender              text NOT NULL,
    message             text,
    ip_address          inet,
    country             text,
    city                text,
    honeypot_triggered  boolean NOT NULL DEFAULT false,
    status              text NOT NULL DEFAULT 'stored',
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_submissions_widget_id ON submissions (widget_id);
CREATE INDEX idx_submissions_tenant_created ON submissions (tenant_id, created_at);
