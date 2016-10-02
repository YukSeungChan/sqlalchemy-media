sqlalchemy-media
================


.. image:: http://img.shields.io/pypi/v/sqlalchemy-media.svg
     :target: https://pypi.python.org/pypi/sqlalchemy-media

.. image:: https://requires.io/github/pylover/sqlalchemy-media/requirements.svg?branch=master
     :target: https://requires.io/github/pylover/sqlalchemy-media/requirements/?branch=master
     :alt: Requirements Status

.. image:: https://travis-ci.org/pylover/sqlalchemy-media.svg?branch=master
     :target: https://travis-ci.org/pylover/sqlalchemy-media

.. image:: https://coveralls.io/repos/github/pylover/sqlalchemy-media/badge.svg?branch=master
     :target: https://coveralls.io/github/pylover/sqlalchemy-media?branch=master

.. image:: https://img.shields.io/badge/license-GPLv3-brightgreen.svg
     :target: https://github.com/pylover/sqlalchemy-media/blob/master/LICENSE



Attaching any files(Image, Video & etc ) into sqlalchemy models using configurable stores including FileSystemStore.

Why ?
-----
Nowadays, most of database applications are requested to allow users to upload and attach files with various types to
ORM models.

Handling those jobs is not simple if you have to care about: Security, High-Availability, Scalability, CDN and more
concerns you already taste those. Accepting a file from public space, analysing, validating, processing(Normalizing)
and making it available to public space again. is the main goal of this project.

Sql-Alchemy is the best platform to implement these stuff on. It has the mutable types to manipulate the objects with
any type in-place. why not ?

Overview
--------

 - Store and locate any file, track it by sqlalchemy models.
 - Storage layer is completely separated from data model, with a simple api: (put, delete, open, locate)
 - Using any SqlAlchemy type. This achieved by using the
`sqlalchemy type decorators <http://docs.sqlalchemy.org/en/latest/core/custom_types.html#typedecorator-recipes>`_.
 - Using `SqlAlchemy mutable <http://docs.sqlalchemy.org/en/latest/orm/extensions/mutable.html>`_.
 - Offering *delete_orphan* flag, to automatically delete files which orphaned via attribute set or delete from
    collections, or objects leaved in memory alone! by setting it's last pointer to None.
 - Attaching files from Url, LocalFileSystem and Streams.
 - Extracting the file's mimetype from the backend stream if possible, using python's built-in
`mimetypes <https://docs.python.org/3.5/library/mimetypes.html>`_ module
 - Limiting file size(min, max), to prevent DOS attacks.

Quick Start
-----------

Here a simple example to how to use this library:
::

    import json
    import functools
    from os.path import join, exists

    from sqlalchemy import Column, Integer, create_engine, Unicode, TypeDecorator
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_media import Image, StoreManager, FileSystemStore


    TEMP_PATH = '/tmp/sqlalchemy-media'
    Base = declarative_base()
    engine = create_engine('sqlite:///:memory:', echo=False)


    # Sqlite is not supporting JSON type, so emulating it:
    class Json(TypeDecorator):
        impl = Unicode

        def process_bind_param(self, value, engine):
            return json.dumps(value)

        def process_result_value(self, value, engine):
            if value is None:
                return None

            return json.loads(value)


    class Person(Base):
        __tablename__ = 'person'
        id = Column(Integer, primary_key=True)
        name = Column(Unicode(100))
        image = Column(Image.as_mutable(Json))

        def __repr__(self):
            return "<%s id=%s>" % (self.name, self.id)


    Base.metadata.create_all(engine, checkfirst=True)
    session_factory = sessionmaker(bind=engine)
    StoreManager.register('fs', functools.partial(FileSystemStore, TEMP_PATH, 'http://static.example.org/'), default=True)

    if __name__ == '__main__':
        session = session_factory()

        with StoreManager(session):
            person1 = Person()
            person1.image = Image.create_from('https://www.python.org/static/img/python-logo@2x.png')
            session.commit()
            print(person1.image)
            path = join(TEMP_PATH, person1.image.path)
            print(path)
            print(person1.image.locate())
            assert exists(path)

Will produces::

    {'key': '48728684-498f-414b-a316-55ff479de4fa', 'contentType': 'image/png', 'length': 15770, 'extension': '.png'}
    /tmp/sqlalchemy-media/images/image-48728684-498f-414b-a316-55ff479de4fa.png
    http://static.example.org/images/image-48728684-498f-414b-a316-55ff479de4fa.png
