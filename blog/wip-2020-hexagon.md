Enter the Hexagon
=================

Questions I'm asking myself as I go forward with refactoring for testability

### How to cope with relationsips between tables when implementig FakeRepos?

Should one preserve the relationsips? Should FakeA know about FakeB if there's an actual table
relation between tables A and B?

For example, should site.organization be a valid way to retrieve an organization?
Should I even attempt to emulate SQLAlchemy objects?
