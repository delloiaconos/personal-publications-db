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

CREATE INDEX "idxDocument_Title" ON "Documents" ("Title");
CREATE INDEX "idxDocument_Category" ON "Documents" ("Category");
CREATE INDEX "idxDocument_Container" ON "Documents" ("Container");

CREATE TABLE IF NOT EXISTS "DocumentIdentifiers" (
	"idDocument" INTEGER NOT NULL,
	"IdentifierType" TEXT NOT NULL,
	"DocumentIdentifier" TEXT NOT NULL UNIQUE,
	CONSTRAINT "pkDocumentIdentifiers" PRIMARY KEY("idDocument","IdentifierType"),
	CONSTRAINT "fkDocumentIdentifiers_idDocument" FOREIGN KEY("idDocument") REFERENCES "Documents"("idDocument")
);

CREATE INDEX "idxDocumentIdentifiers_IdentifierType" ON "DocumentIdentifiers" ("IdentifierType");
CREATE INDEX "idxDocumentIdentifiers_DocumentIdentifier" ON "DocumentIdentifiers" ("DocumentIdentifier");

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

CREATE INDEX "idxDocumentTags_DocumentTag" ON "DocumentTags" ("DocumentTag");

COMMIT;
