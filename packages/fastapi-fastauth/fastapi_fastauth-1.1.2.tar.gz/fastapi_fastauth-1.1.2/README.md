# FastAuth
<p align="center">
  <img src="https://raw.githubusercontent.com/AstralMortem/fastauth/master/logo.png?sanitize=true" alt="FastAuth">
</p>

<p align="center">
    <em>Ready-to-use customizable solution for FastAPI with Authentication, Authorization(RBAC) and OAuth2 support</em>
</p>

---
## About

[![CI](https://github.com/AstralMortem/fastauth/actions/workflows/ci.yaml/badge.svg)](https://github.com/AstralMortem/fastauth/actions/workflows/ci.yaml)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/AstralMortem/fastauth/docs.yaml?label=Docs)](https://astralmortem.github.io/fastauth/)
[![codecov](https://codecov.io/github/AstralMortem/fastapi-fastauth/graph/badge.svg?token=SI6ND9SIPU)](https://codecov.io/github/AstralMortem/fastapi-fastauth)
[![PyPI - Version](https://img.shields.io/pypi/v/fastapi-fastauth)](https://pypi.org/project/fastapi-fastauth/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/fastapi-fastauth)](https://pypi.org/project/fastapi-fastauth/)


Here’s a ready-to-use, customizable solution for FastAPI with Authentication, Authorization (RBAC), and OAuth2 support.
This solution provides token based authentication(JWT, Redis, DB), role-based access control, and OAuth2 integration.
Highly inspired by [FastAPI Users](https://github.com/fastapi-users/fastapi-users) and [AuthX](https://github.com/yezz123/authx/tree/main):

* **Documentation**: <https://astralmortem.github.io/fastapi-fastauth/>
* **Source Code**: <https://github.com/AstralMortem/fastapi-fastauth>
---

## Features

* [x] Authentication:
    * [x] Access and Refresh Token Dependencies
    * [x] Different Token Strategy(JWT, Redis, Database)
    * [x] Different Token locations(Header, Cookie, Query, etc.)
* [x] Authorization:
    * [x] Roles and Permission support
    * [x] OAuth2 support
* [x] User Management:
    * [x] User Model protocol
    * [x] Service-Repository pattern for flexible customization
    * [x] Popular ORM support:
        * [x] SQLAlchemy support
        * [ ] Beanie
        * [ ] Tortoise ORM
