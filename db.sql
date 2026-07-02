BEGIN TRANSACTION;

-- Author's related tables

CREATE TABLE IF NOT EXISTS "Authors" (
	"idAuthor" INTEGER NOT NULL UNIQUE,
	"FirstName" TEXT NOT NULL,
	"LastName" TEXT NOT NULL,
	"MiddleName" TEXT,
	PRIMARY KEY("idAuthor" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "AuthorIdentifiers" (
	"idAuthor" INTEGER NOT NULL,
	"IdentifierType" TEXT NOT NULL,
	"AuthorIdentifier" TEXT NOT NULL UNIQUE,
	CONSTRAINT "fkAuthorIdentifiers_idAuthor" FOREIGN KEY("idAuthor") REFERENCES "Authors"("idAuthor")
);

-- Document's related tables

CREATE TABLE IF NOT EXISTS "Documents" (
	"idDocument" INTEGER NOT NULL UNIQUE,
	"Title" BLOB NOT NULL,
	"Category" TEXT NOT NULL,
	"Container" TEXT NOT NULL,
	PRIMARY KEY("idDocument" AUTOINCREMENT)
);

CREATE INDEX IF NOT EXISTS "idxDocument_Title" ON "Documents" ("Title");
CREATE INDEX IF NOT EXISTS "idxDocument_Category" ON "Documents" ("Category");
CREATE INDEX IF NOT EXISTS "idxDocument_Container" ON "Documents" ("Container");

CREATE TABLE IF NOT EXISTS "DocumentIdentifiers" (
	"idDocument" INTEGER NOT NULL,
	"IdentifierType" TEXT NOT NULL,
	"DocumentIdentifier" TEXT NOT NULL UNIQUE,
	CONSTRAINT "pkDocumentIdentifiers" PRIMARY KEY("idDocument","IdentifierType"),
	CONSTRAINT "fkDocumentIdentifiers_idDocument" FOREIGN KEY("idDocument") REFERENCES "Documents"("idDocument")
);

CREATE INDEX IF NOT EXISTS "idxDocumentIdentifiers_IdentifierType" ON "DocumentIdentifiers" ("IdentifierType");

CREATE TABLE IF NOT EXISTS "DocumentAuthors" (
	"idDocument" INTEGER NOT NULL,
	"idAuthor" INTEGER NOT NULL,
	"AuthOrder"	INTEGER DEFAULT 0,
	CONSTRAINT "pkDocumentAuthors" PRIMARY KEY("idDocument","idAuthor"),
	CONSTRAINT "fkDocumentAuthors_idAuthor" FOREIGN KEY("idAuthor") REFERENCES "Authors"("idAuthor"),
	CONSTRAINT "fkDocumentAuthors_idDocument" FOREIGN KEY("idDocument") REFERENCES "Documents"("idDocument")
);

CREATE TABLE IF NOT EXISTS "DocumentTags" (
	"idDocument" INTEGER NOT NULL,
	"DocumentTag" TEXT NOT NULL,
	CONSTRAINT "pkDocumentTags" PRIMARY KEY("idDocument","DocumentTag"),
	CONSTRAINT "fkDocumentTags_idDocument" FOREIGN KEY("idDocument") REFERENCES "Documents"("idDocument")
);

CREATE INDEX IF NOT EXISTS "idxDocumentTags_DocumentTag" ON "DocumentTags" ("DocumentTag");

CREATE TABLE IF NOT EXISTS "DocumentKeywords" (
	"idDocument" INTEGER NOT NULL,
	"Keyword" TEXT NOT NULL,
	CONSTRAINT "pkDocumentKeywords" PRIMARY KEY("idDocument","Keyword"),
	CONSTRAINT "fkDocumentKeywords_idDocument" FOREIGN KEY("idDocument") REFERENCES "Documents"("idDocument")
);

CREATE INDEX IF NOT EXISTS "idxDocumentKeywords_Keyword" ON "DocumentKeywords" ("Keyword");

COMMIT;
