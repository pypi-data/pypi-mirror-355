%define srcname dqsegdb
%define version 3.0.0
%define release 1

Name: python-%{srcname}
Version: %{version}
Release: %{release}%{?dist}
Summary: Client library for DQSegDB
Vendor: Robert Bruntz <robert.bruntz@ligo.org>

License: GPLv3
Url:     https://git.ligo.org/computing/dqsegdb/client
Source0: %pypi_source

BuildArch: noarch
Prefix: %{_prefix}

# build requirements
BuildRequires: python%{python3_pkgversion}-devel
BuildRequires: python%{python3_pkgversion}-pip
BuildRequires: python%{python3_pkgversion}-setuptools
BuildRequires: python%{python3_pkgversion}-wheel

# -- src.rpm

%description
This package provides the client tools to connect to LIGO/VIRGO
DQSEGDB server instances.
Binary RPMs are split into the Python libraries in the
'python*-dqsegdb' package(s) and the command-line tools in the
'dqsegdb' package.

# -- dqsegdb

%package -n %{srcname}
Summary: %{summary}
BuildArch: noarch
Requires: python%{python3_pkgversion}-%{srcname} = %{version}-%{release}
%description -n %{srcname}
This package provides the client tools to connect to LIGO/VIRGO
DQSEGDB server instances.

# -- python3x-dqsegdb

%package -n python%{python3_pkgversion}-%{srcname}
Summary: Python %{python3_version} client library for the DQSEGDB service
Requires: python%{python3_pkgversion}-gpstime
Requires: python%{python3_pkgversion}-igwn-auth-utils
Requires: python%{python3_pkgversion}-lal
Requires: python%{python3_pkgversion}-igwn-segments
Requires: python%{python3_pkgversion}-lscsoft-glue >= 3.0.1
Requires: python%{python3_pkgversion}-pyOpenSSL >= 0.14
Requires: python%{python3_pkgversion}-pyRXP
%{?python_provide:%python_provide python%{python3_pkgversion}-%{srcname}}
%description -n python%{python3_pkgversion}-%{srcname}
Python %{python3_version} interface libraries for the DQSEGDB client
tools.

# -- build

%prep
%autosetup -n %{srcname}-%{version}

%build
# remove the lalsuite requirement from setup.py, that is fulfilled by
# python3-lal RPMs
sed -i '/lalsuite/d' setup.py
# build the wheel
%py3_build_wheel

%install
%py3_install_wheel %{srcname}-%{version}-*.whl

%check
# print the metadata
PATH="%{buildroot}%{_bindir}:${PATH}" \
%{__python3} -m pip show dqsegdb

%clean
rm -rf $RPM_BUILD_ROOT

# -- files

%files -n %{srcname}
%defattr(-,root,root)
%license LICENSE
%doc README.md
%{_bindir}/*dqsegdb

%files -n python%{python3_pkgversion}-dqsegdb
%defattr(-,root,root)
%license LICENSE
%doc README.md
%{python3_sitelib}/*

# -- changelog

%changelog

* Fri Jun 13 2025 Robert Bruntz <robert.bruntz@ligo.org> 3.0.0-1
- major new version
- replaced python3-ligo-segments with python3-igwn-segments
- removed restriction python3-lscsoft-glue < 4.0.0

* Tue Apr 22 2025 Robert Bruntz <robert.bruntz@ligo.org> 2.2.0-1
- changes to code, esp. SciTokens usage; no packaging changes

* Tue Feb 06 2024 Robert Bruntz <robert.bruntz@ligo.org> 2.1.0-1
- update RPM build/install to use wheels
- remove references to (removed) user-env scripts
- disable pytest during RPM/Deb builds
- pin lscsoft-glue to >= 3.0.1, < 4.0.0

* Thu Jan 27 2022 Robert Bruntz <robert.bruntz@ligo.org> 2.0.0-1
- added python3-lal as a requirement for python3-dqsegdb

* Tue Dec 7 2021 Duncan Macleod <duncan.macleod@ligo.org> 1.6.1-2
- build python3 packages
- bundle command-line tools separately
