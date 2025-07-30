# Copyright (C) 2024 Maxwell G <maxwell@gtmx.me>
# SPDX-License-Identifier: MIT
# License text: https://spdx.org/licenses/MIT

Name:           python-zstarfile
Version:        0.3.0
Release:        1%{?dist}
Summary:        tarfile extension with additional compression algorithms and PEP 706 by default


License:        MIT
URL:            https://sr.ht/~gotmax23/zstarfile
%global furl    https://git.sr.ht/~gotmax23/zstarfile
Source0:        %{furl}/refs/download/v%{version}/zstarfile-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  gnupg2
BuildRequires:  python3-devel

Recommends:     %{py3_dist zstarfile[all]}

%global _description %{expand:
zstarfile is a tarfile extension with additional compression algorithms and
PEP 706 by default.}

%description %_description

%package -n python3-zstarfile
Summary:        %{summary}

%description -n python3-zstarfile %_description


%prep
%autosetup -p1 -n zstarfile-%{version}


%generate_buildrequires
%pyproject_buildrequires -x all,lz4,zstandard,test


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files zstarfile


%check
# ERROR_FOR_MISSING makes it so the tests don't try to use pytest.importorskip
# which doesn't support exc_type on EL 9's old pytest version and causes an error.
%{?el9:export ERROR_FOR_MISSING=1}
%pytest


%files -n python3-zstarfile -f %{pyproject_files}
%doc README.md
%license LICENSES/*

%pyproject_extras_subpkg -n python3-zstarfile all lz4 zstandard

%changelog

* Mon Jun 16 2025 Maxwell G <maxwell@gtmx.me> - 0.3.0-1
- Release 0.3.0.

* Sun Apr 07 2024 Maxwell G <maxwell@gtmx.me> - 0.2.0-1
- Release 0.2.0.

* Sat Apr 06 2024 Maxwell G <maxwell@gtmx.me> - 0.0.1-1
- Initial package
