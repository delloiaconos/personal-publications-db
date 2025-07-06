BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "AuthorIdentifiers" (
	"idAuthor"	INTEGER NOT NULL,
	"IdentifierType"	TEXT NOT NULL,
	"AuthorIdentifier"	TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "Authors" (
	"idAuthor"	INTEGER NOT NULL UNIQUE,
	"FirstName"	TEXT NOT NULL,
	"LastName"	TEXT NOT NULL,
	"MiddleName"	TEXT,
	PRIMARY KEY("idAuthor" AUTOINCREMENT),
	CONSTRAINT "fkAuthodsId_idAutor" FOREIGN KEY("idAuthor") REFERENCES "Authors"("idAuthor")
);
CREATE TABLE IF NOT EXISTS "DocumentAuthors" (
	"idDocument"	INTEGER NOT NULL,
	"idAuthor"	INTEGER NOT NULL,
	"AuthOrder"	INTEGER DEFAULT 0,
	CONSTRAINT "pkDocAuth" PRIMARY KEY("idDocument","idAuthor")
);
CREATE TABLE IF NOT EXISTS "DocumentIdentifiers" (
	"idDocument"	INTEGER NOT NULL,
	"IdentifierType"	TEXT NOT NULL,
	"DocumentIdentifier"	TEXT NOT NULL UNIQUE,
	CONSTRAINT "fkDocIde_idDoc" FOREIGN KEY("idDocument") REFERENCES ""
);
CREATE TABLE IF NOT EXISTS "Documents" (
	"idDocument"	INTEGER NOT NULL UNIQUE,
	"Title"	BLOB NOT NULL,
	"Category"	TEXT NOT NULL,
	"Container" TEXT NOT NULL,
	PRIMARY KEY("idDocument" AUTOINCREMENT)
);
COMMIT;
