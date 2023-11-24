Name:                 ibus-typing-booster
Version:              2.1.0
Release:              5%{?dist}
Summary:              A completion input method
License:              GPLv3+
Group:                System Environment/Libraries
URL:                  https://mike-fabian.github.io/ibus-typing-booster/
Source0:              https://github.com/mike-fabian/ibus-typing-booster/releases/download/%{version}/ibus-typing-booster-%{version}.tar.gz
Patch0:               gating.patch
Patch1:               Prevent-also-BackSpace-from-reopening-a-preedit-when.patch
Requires:             ibus >= 1.5.3
Requires:             m17n-lib
Requires:             python(abi) >= 3.3
%{?__python3:Requires: %{__python3}}
Requires:             python3-dbus
Requires:             python3-enchant
Requires:             python3-pyxdg
%if 0%{?fedora} >= 24 || 0%{?rhel} > 7
# Recommend reasonably good fonts which have most of the emoji:
%if 0%{?fedora} <= 26
Recommends:           google-noto-emoji-fonts
%endif
Recommends:           google-noto-emoji-color-fonts
Recommends:           gdouros-symbola-fonts
%endif
%if 0%{?fedora} >= 26 || 0%{?rhel} > 7
# Save some space in the binary rpm by requiring the Fedora
# packages which contain the emoji data files:
Requires:             cldr-emoji-annotation
Requires:             unicode-ucd
%endif
BuildRequires:        ibus-devel
%if 0%{?fedora} >= 24 || 0%{?rhel} > 7
BuildRequires:        python3-devel
BuildRequires:        python3-pyxdg
%else
BuildRequires:        python34-devel
%endif
# for the unit tests
BuildRequires:        m17n-lib
BuildRequires:        m17n-db-extras
BuildRequires:        python3-enchant
BuildRequires:        libappstream-glib
BuildRequires:        desktop-file-utils
BuildRequires:        python3-gobject
BuildRequires:        python3-gobject-base
BuildRequires:        hunspell-cs
BuildRequires:        hunspell-de
BuildRequires:        hunspell-en
BuildRequires:        hunspell-es
BuildRequires:        hunspell-fr
BuildRequires:        hunspell-it
BuildRequires:        hunspell-ko
BuildRequires:        glib2
BuildRequires:  desktop-file-utils
BuildRequires:  python3-gobject
BuildRequires:  gtk3
BuildRequires:  dbus-x11
BuildRequires:  dconf
BuildRequires:  ibus
BuildRequires:        gtk3
BuildRequires:        dconf
BuildRequires:        dbus-x11
BuildRequires:        ibus
BuildArch:            noarch

%description
Ibus-typing-booster is a context sensitive completion
input method to speedup typing.

%package tests
Summary:              Tests for the %{name} package
Requires:             %{name} = %{version}-%{release}

%description tests
The %{name}-tests package contains tests that can be used to verify
the functionality of the installed %{name} package.

%package -n emoji-picker
Summary:              An emoji selection tool
Requires:             ibus-typing-booster = %{version}-%{release}

%description -n emoji-picker
A simple application to find and insert emoji and other
Unicode symbols.

%prep
%setup -q
%patch0 -p1 -b .gating
%patch1 -p1 -b .backspace

%build
export PYTHON=%{__python3}
%configure --disable-static --disable-additional
make %{?_smp_mflags}

%install 
export PYTHON=%{__python3}
make install DESTDIR=${RPM_BUILD_ROOT} NO_INDEX=true  INSTALL="install -p"   pkgconfigdir=%{_datadir}/pkgconfig
%if 0%{?fedora} >= 26 || 0%{?rhel} > 7
    # These files are in the required package “cldr-emoji-annotation”
    rm $RPM_BUILD_ROOT/%{_datadir}/%{name}/data/annotations/*.xml
    rm $RPM_BUILD_ROOT/%{_datadir}/%{name}/data/annotationsDerived/*.xml
    # This file is in the required package “unicode-ucd”:
    rm $RPM_BUILD_ROOT/%{_datadir}/%{name}/data/UnicodeData.txt
    # At least emoji-data.txt emoji-sequences.txt emoji-zwj-sequences.txt
    # are still there even on Fedora >= 26 they are not available in any packages:
    gzip -n --force --best $RPM_BUILD_ROOT/%{_datadir}/%{name}/data/*.txt
    # The json file from emojione is not deleted anymore because
    # the package nodejs-emojione-json has been orphaned:
    gzip -n --force --best $RPM_BUILD_ROOT/%{_datadir}/%{name}/data/*.json
%else
    gzip -n --force --best $RPM_BUILD_ROOT/%{_datadir}/%{name}/data/*.{txt,json}
    gzip -n --force --best $RPM_BUILD_ROOT/%{_datadir}/%{name}/data/annotations/*.xml
    gzip -n --force --best $RPM_BUILD_ROOT/%{_datadir}/%{name}/data/annotationsDerived/*.xml
%endif

mkdir -p $RPM_BUILD_ROOT/%{_libexecdir}/installed-tests/%{name}
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/installed-tests/%{name}
make -C tests run_tests
cp tests/run_tests $RPM_BUILD_ROOT/%{_libexecdir}/installed-tests/%{name}
cp tests/test_itb.py $RPM_BUILD_ROOT/%{_libexecdir}/installed-tests/%{name}
cat <<EOF > $RPM_BUILD_ROOT/%{_datadir}/installed-tests/%{name}/test_itb.test
[Test]
Type=session
Exec=/usr/libexec/installed-tests/ibus-typing-booster/run_tests test_itb.py
Output=TAP
EOF

%find_lang %{name}

%check
export LC_ALL=en_US.UTF-8
appstream-util validate-relax --nonet %{buildroot}/%{_datadir}/metainfo/*.appdata.xml
desktop-file-validate \
    $RPM_BUILD_ROOT%{_datadir}/applications/ibus-setup-typing-booster.desktop
desktop-file-validate \
    $RPM_BUILD_ROOT%{_datadir}/applications/emoji-picker.desktop
pushd engine
    # run doctests
    python3 hunspell_suggest.py
    python3 m17n_translit.py
    python3 itb_emoji.py
    python3 itb_util.py
popd
mkdir -p /tmp/glib-2.0/schemas/
cp org.freedesktop.ibus.engine.typing-booster.gschema.xml \
   /tmp/glib-2.0/schemas/org.freedesktop.ibus.engine.typing-booster.gschema.xml
glib-compile-schemas /tmp/glib-2.0/schemas #&>/dev/null || :
export XDG_DATA_DIRS=/tmp
eval $(dbus-launch --sh-syntax)
dconf dump /
dconf write /org/freedesktop/ibus/engine/typing-booster/offtherecord false
dconf write /org/freedesktop/ibus/engine/typing-booster/usedigitsasselectkeys true
dconf write /org/freedesktop/ibus/engine/typing-booster/addspaceoncommit true
dconf write /org/freedesktop/ibus/engine/typing-booster/tabenable false
dconf write /org/freedesktop/ibus/engine/typing-booster/inputmethod "'NoIme'"
dconf write /org/freedesktop/ibus/engine/typing-booster/rememberlastusedpreeditime true
dconf write /org/freedesktop/ibus/engine/typing-booster/mincharcomplete 1
dconf write /org/freedesktop/ibus/engine/typing-booster/dictionary "'en_US'"
dconf write /org/freedesktop/ibus/engine/typing-booster/emojipredictions true
dconf write /org/freedesktop/ibus/engine/typing-booster/autocommitcharacters "''"
dconf write /org/freedesktop/ibus/engine/typing-booster/pagesize 6
dconf write /org/freedesktop/ibus/engine/typing-booster/shownumberofcandidates true
dconf write /org/freedesktop/ibus/engine/typing-booster/showstatusinfoinaux true
dconf dump /
ibus-daemon -drx
make check || cat ./tests/test-suite.log

%post
[ -x %{_bindir}/ibus ] && \
  %{_bindir}/ibus write-cache --system &>/dev/null || :

%postun
[ -x %{_bindir}/ibus ] && \
  %{_bindir}/ibus write-cache --system &>/dev/null || :

%files -f %{name}.lang
%doc AUTHORS COPYING README
%{_datadir}/%{name}
%{_datadir}/metainfo/typing-booster.appdata.xml
%{_datadir}/ibus/component/typing-booster.xml
%{_datadir}/icons/hicolor/16x16/apps/ibus-typing-booster.png
%{_datadir}/icons/hicolor/22x22/apps/ibus-typing-booster.png
%{_datadir}/icons/hicolor/32x32/apps/ibus-typing-booster.png
%{_datadir}/icons/hicolor/48x48/apps/ibus-typing-booster.png
%{_datadir}/icons/hicolor/64x64/apps/ibus-typing-booster.png
%{_datadir}/icons/hicolor/128x128/apps/ibus-typing-booster.png
%{_datadir}/icons/hicolor/256x256/apps/ibus-typing-booster.png
%{_datadir}/icons/hicolor/scalable/apps/ibus-typing-booster.svg
%{_libexecdir}/ibus-engine-typing-booster
%{_libexecdir}/ibus-setup-typing-booster
%{_datadir}/applications/ibus-setup-typing-booster.desktop
%{_datadir}/glib-2.0/schemas/org.freedesktop.ibus.engine.typing-booster.gschema.xml

%files tests
%dir %{_libexecdir}/installed-tests
%{_libexecdir}/installed-tests/%{name}
%dir %{_datadir}/installed-tests
%{_datadir}/installed-tests/%{name}

%files -n emoji-picker
%{_bindir}/emoji-picker
%{_datadir}/applications/emoji-picker.desktop


%changelog
* Fri Nov 24 2023 Michael L. Young <elgueromexicano@gmail.com> - 2.1.0
- Add missing BuildRequires for unit tests

* Thu Feb 04 2021 Mike FABIAN <mfabian@redhat.com> - 2.1.0-5
- Prevent also BackSpace from reopening a preedit when the
  option “Arrow keys can reopen a preedit” is off
- Resolves: rhbz#1925030

* Tue Jun 09 2020 Mike FABIAN <mfabian@redhat.com> - 2.1.0-4
- Add gating tests
- Resolves: rhbz#1682164

* Tue Oct 09 2018 Mike FABIAN <mfabian@redhat.com> - 2.1.0-3
- Make “make check“ test cases work again when building the rpm
  (To avoid that rpmdiff in the errata tool reports a problem)
- Related: rhbz#1619153

* Thu Sep 20 2018 Tomas Orsava <torsava@redhat.com> - 2.1.0-2
- Require the Python interpreter directly instead of using the package name
- Related: rhbz#1619153

* Tue Jul 24 2018 Mike FABIAN <mfabian@redhat.com> - 2.1.0-1
- Update to 2.1.0
- emoji-picker: Show a concise description of a selected emoji in the header bar
- Update the setup UI when settings are changed outside of the setup UI
- Migrate IBusConfig to GSettings (The old settings are
  unfortunately lost, so one has to open the setup tool
  and recreate ones favourite settings).
- Read emoji data files always in UTF-8

* Wed Jun 27 2018 Mike FABIAN <mfabian@redhat.com> - 2.0.2-1
- Update to 2.0.2
- Better Tab handling, use Tab to switch to the next candidate, not to commit
- Update to 2.0.1
- Update translations from zanata (ja updated)
- Update emoji annotations from CLDR
- Fix some bugs in the usage of “prefix” for prefixes other than “/usr” (For FreeBSD)
- Make itb_util.get_ime_help() work on FreeBSD
- Update UnicodeData.txt to Unicode 11.0.0
- Remove useless 't-nil vi-base': 'vi-base.mim', from M17N_INPUT_METHODS
- Remove extra space in entry for sa-IAST input method to make it work
- Show in the setup tool in the input listbox whether minput_open_im() succeeded.
- Use the rocket icon emoji_u1f680.svg from the “Noto Color Emoji” font

* Mon May 28 2018 Mike FABIAN <mfabian@redhat.com> - 2.0.0-1
- Update to 2.0.0
- Update translations because of the merge of the engines (de, pl, uk updated)
- Update emoji annotations from CLDR
- Do not hardcode icon names in desktop files
  (Resolves: https://github.com/mike-fabian/ibus-typing-booster/issues/17)
- Change the default for “Unicode symbols and emoji predictions” to “False”
- Merge all typing-booster engines into one
- Change the UI of the setup tool to make it possible to select
  multiple input methods and dictionaries
- Move the buttons to learn from a file and to delete learned data to the options tab
- Use the same “About” dialog in the setup tool as in emoji-picker

* Tue May 22 2018 Mike FABIAN <mfabian@redhat.com> - 1.5.38-2
- Update to 1.5.38
- Refresh french translation (thanks to Thierry Thomas)
- Mark comments in the emoji-picker about dialog as translatable

* Mon May 14 2018 Mike FABIAN <mfabian@redhat.com> - 1.5.37-1
- Update to 1.5.37
- Update translations from Zanata (pl and uk updated)
- Make “Add direct input” option work correctly when
  “Remember last preedit input method” option is off
- Fix test case for Korean
- Rewrite setup UI completely in Python, without using Glade
- Fix format string in debug message when a dictionary .aff file has no encoding
  (Resolves: rhbz#1575659)
- Return False in read_training_data_from_file() if file cannot be opened

* Tue Apr 10 2018 Mike FABIAN <mfabian@redhat.com> - 1.5.36-1
- Update to 1.5.36
- Make the default for self.show_status_info_in_auxiliary_text False
  (Resolves: rhbz#156435)
- Adapt hunspell_suggest.py to work with pyhunspell 0.5.4

* Wed Mar 07 2018 Mike FABIAN <mfabian@redhat.com> - 1.5.35-1
- Update to 1.5.35
- Update translations from zanata (es, pl and uk updated)
- Update UnicodeData.txt to UnicodeData-11.0.0d13.txt
- Read also the emoji names from the emoji-test.txt file
- Update Unicode emoji data to a prerelease of Unicode Emoji Data 11.0
- Fix PyGTKDeprecationWarning: Using positional arguments with the GObject constructor has been deprecat
-d.
- Add “Twemoji” as a good colour emoji font to the emoji-picker font list
- Don’t show the languages en_001 and  es_419 in the browsing treeview
- Use romaji=True by default in EmojiMatcher
- Update emoji annotations from CLDR
- Fix Source URL in spec file, fedorahosted is retired.
- Use gzip -n to not include build timestamps in .gz headers

* Fri Feb 09 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 1.5.34-4
- Escape macros in %%changelog

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.34-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Jan 02 2018 Troy Dawson <tdawson@redhat.com> - 1.5.34-2
- Update conditionals

* Thu Oct 05 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.34-1
- update to 1.5.34
- Update translations from zanata (cs new, de updated)
- Add some tooltips
- Add an option whether to use pango font fallback to emoji-picker
- Update emoji annotations from CLDR
- Add Recommends: google-noto-emoji-color-fonts

* Mon Sep 11 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.33-1
- update to 1.5.33
- Update translations from zanata (es new)
- Install appstream metadata to /usr/share/metainfo/
- Update UnicodeData.txt to Unicode 10.0.0
- Fix test cases and kakasi support for the update of the
  emoji annotations from CLDR
- Update emoji annotations from CLDR
- Skip the emoji which already have skin tone modifiers
  in itb_emoji.emoji_by_label()
- Never load characters of Unicode categories “Cc”, “Co”,
  and “Cs” into the emoji dictionary
- Update emoji-data.txt to 5.0

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.5.32-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Apr 24 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.32-2
- Do not require nodejs-emojione-json anymore, that package has been orphaned

* Mon Apr 24 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.32-1
- update to 1.5.32
- Fix error when starting emoji-picker when the “recently-used” does not yet exist
- Update emojione.json to version 3.0
- Add the data from CLDR common/annotationsDerived
- Load also the CLDR annotations from “annotationsDerived”

* Tue Apr 18 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.31-1
- update to 1.5.31
- Rename option --use_vs16 to --non_fully_qualified
  (effectivly reversing the default)
- Make description labels in info popover selectable to be able
  to copy and paste their contents
- Sort similar emoji with the same number of matching labels
  by cldr_order distance
- Map cldr subgroup 'person-sport' to emojione category 'activity'
- Make the categorie listings and the search work right
  when using --use_vs16
- Always store only non-fully-qualified emoji or emoji-sequences
  in the internal dictionary
- Update emoji annotations from CLDR

* Mon Mar 27 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.30-1
- update to 1.5.30
- Update translations from zanata (de, pl, uk updated)
- Use string order as a fallback to cldr_order in category listings
- The rainbow flag should be a zwj sequence
- Also display the Unicode version in the emoji info popover
- When looking up emoji or other characters via Unicode codepoint,
  ignore surrogates and private use characters
- Show the fonts really used to render an emoji in the
  info popover for the emoji
- Fix typo in translatable string
- itb_emoji.py: Use CLDR order to sort the candidates and
  the similar emoji if score is the same

* Mon Mar 20 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.29-1
- update to 1.5.29
- Add Recommends: google-noto-emoji-fonts, “Noto Color Emoji”
  looks much better than “Symbola” even in gray scale.
- Update translations from zanata (de, pl updated)
- Add a “--version” command line option to emoji-picker
- itb_emoji.py: Also read emoji-test.txt (from unicode.org)
- emoji-picker: Set default font to first available in
  ['Noto Color Emoji', 'Emoji One', 'Symbola']
- Small parsing improvement of emoji-sequences.txt
- Add support to either use U+FE0F VARIATION SELECTOR-16 in emoji sequences or not
- emoji-picker: Show “∅ Search produced empty result.” when nothing matches in a search

* Sat Mar 18 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.28-1
- update to 1.5.28
- Allow query by code point even if Python’s unicodedata.name()
  does not know the character
- Also read names from emoji-sequences.txt and emoji-zwj-sequences.txt
- itb_emoji.py: Also read emoji-sequences.txt (from unicode.org)
- Fix positioning of info popover (fix a typo in an “if” statement)
- Show emoji properties from unicode.org when debugging is on
- itb_emoji.py: Also read emoji-zwj-sequences.txt (from unicode.org)
- Also use the emoji properties from unicode.org to decide whether
  to offer a lookup on emojipedia
- Use property “Emoji_Modifier_Base” from emoji-data.txt to check
  whether an emoji supports skin tones
- itb_emoji.py: Also read emoji-data.txt (from unicode.org)
- Tentative skin tone support for families
- Improve skin tone support: make it work for professions (roles) as well
- Make skin tone popover scrollable and limit its maximum size

* Fri Mar 17 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.27-1
- update to 1.5.27
- Update translations from zanata (pl, uk updated)
- emoji-picker: make skin tone selection work for gendered emoji

* Thu Mar 16 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.26-1
- update to 1.5.26
- Update translations from zanata (de updated)
- Fix display of warning message when a dictionary is not installed.
- Emulate xdg.BaseDirectory.save_data_path() on systems which lack pyxdg
- Show the skin tone popover also on a long press gesture
- Fix pyhunspell support
  Resolves: https://github.com/mike-fabian/ibus-typing-booster/issues/5#issuecomment-286251818

* Mon Mar 13 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.25-1
- update to 1.5.25
- on Fedora 26, save some space in the binary rpm by requiring the
  Fedora packages which contain the emoji data files
- Update translations from zanata (de, pl, uk updated, zh_CN new)
- Show the categories as well on right mouse click in emoji-picker
- Improve information displayed on right mouse click in emoji-picker
- html.unescape() the strings parsed from the cldr annotations
- Fix fontsize change for invisible emoji in browse flowbox
- Add an option whether the arrow keys are allowed to reopen a preëdit
- Add an option to work around the broken forward_key_event()
  in the Qt 4/5 im module
- Use xdg.BaseDirectory to add a USER_DATADIR to the
  search path for data for itb_emoji.py
- emoji_picker.py: Speedup: Fix wrong indentation of block
  in _fill_flowbox_browse()
- emoji_picker.py: Print some profiling information when debugging is enabled
- Store the clipboard with gtk_clipboard_store() to keep it around
  after emoji-picker quits
- emoji-picker: Do not override the decoration layout of the header bar
- When an emoji with a different skin tone is selected,
  replace the original emoji immediately
- Make emoji-picker work on dark themes like Adwaita-dark as well

* Mon Mar 06 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.24-1
- update to 1.5.24
- Update translations from zanata (de updated)
- The spin button to change the fontsize should grab focus without selecting
- emoji-picker: Don’t check if ibus is running,
  ibus does not need to run for emoji-picker
- Load .desktop files for emoji-picker and ibus-setup-typing-booster
  correctly under Gnome Wayland
- Show the most recently used skin tone by default
- Use Popovers for skin tones
- Don’t use HeaderBar with the default widget titlebar
- Display the detailed information of an emoji as a popover, not as a tooltip
- Use CSS to show light gray borders around flowbox and listbox children
- create emoji-picker sub-package (Resolves: rhbz#1429154)

* Mon Feb 27 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.23-1
- update to 1.5.23
- Update translations from zanata (de, ja, pl, uk updated)
- emoji_picker.py: Add a menu button to change the font for the emoji
- emoji-picker: Make background colour of the flowbox listing the emoji white
- emoji-picker: Use “Symbola” as the default font
- Remember the font and the fontsize in a config file
- emoji_picker.py: Add a spin button to change the font size of the emoji
- Add option to the emoji-picker to load *all* Unicode characters
- UI redesign of the emoji-picker
- Return an empty list immediately if candidates() is called with an empty search string
- Make the fontsize for the names of the emoji in the search results smaller
- Make the search in emoji-picker a bit more responsive by using GLib.idle_add()
- Save the recently used emoji immediately, not only when the program quits
- Set default font size of emoji-picker to 24 instead of 16
- Set the emoji font only for the emoji, not for its name in the search results
- Set WM_CLASS of emoji-picker and ibus-setup-typing-booster correctly
- Add “Icon” and “Categories” to emoji-picker.desktop

* Wed Feb 22 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.22-1
- update to 1.5.22
- Update translations from zanata (de, fr, pl, uk updated)
- Add an emoji-picker
- Update of en.xml from CLDR’s emoji annotations
- Fix skipping of the Korean test case when no Korean dictionary can be found
- Fix invalid xml in typing-booster.appdata.xml
- add Requires: python3-pyxdg (for the emoji-picker)

* Tue Feb 07 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.21-1
- update to 1.5.21
- add BuildRequires:  hunspell-fr (for make check)
- Handle Return and Enter correctly when the cursor is not at
  the end of the preëdit (Resolves: rhbz#1418313)
- Values of spin buttons should not be translatable
- Make the categories from emojione translatable
- Make emoji matching accent insensitive
- If available use pykakasi to convert Japanese emoji category
  names to hiragana
- If available use the “pinyin” Python module to add pinyin
  to the Chinese names and keywords
- Don’t fallback to “zh” from “zh_TW”, “zh_HK”, “zh_MO” and “zh_Hant”
- Don’t sort the labels when listing similar emoji
- Don’t change Unicode categories to lowercase when loading,
  use the original case
- Also treat categories 'Zl' and 'Zp' as invisible and add
  Unicode code point
- When searching for similar emoji, the original emoji should be
  most similar to itself
- Fix duplicate listing of labels when looking up similar emoji
- Make it optionally possible to match emoji in Japanese using romaji
- itb_emoji.py: Add the code point to the name of invisible
  characters also when looking up similar characters
- Better matching of the Unicode categories
- Small performance optimization in EmojiMatcher.similar()
- Remove any U+2028 LINE SEPARATOR and U+2029 PARAGRAPH SEPARATOR characters
  from the lookup table
- Nicer display of the matching labels when looking up similar emoji
- Don’t strip mathematical symbols (category 'Sm') from tokens
- Update of en.xml from CLDR’s emoji annotations
- Update translations from zanata (de, pl updated)

* Thu Jan 26 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.20-1
- update to 1.5.20
- Calculate the maximum word length for each dictionary individually
- Use .startswith instead of regexp matching when matching in hunspell
  dictionaries (speed optimization)
- Improve accent insensitive matching (“filosofičtějš” should also
  match “filosofičtější”)
- Some updates for the emoji annotations in en.xml from CLDR

* Thu Jan 19 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.19-2
- update to 1.5.19
- Improve setup layout (thanks to Trinh Anh Ngoc <atw1990@gmail.com>)
- Add some more directories to search for dictionaries (for FreeBSD)
- Wrong variable “page_size” was used in set_lookup_table_orientation()
- Do not try to reopen the preëdit when any modifier except
  CapsLock is on (Resolves: rhbz#1414642)

* Tue Jan 17 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.18-1
- update to 1.5.18
- Fix typo in the “Unbreak sqlite on Python 3.6” patch
- Fix the fallback to use pyhunspell-python3 when python3-enchant
  is not available
- Remove useless ibus-typing-booster.pc

* Fri Jan 13 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.17-1
- update to 1.5.17
- Update py-compile to current upstream version
- Also use ＿ U+FF3F FULLWIDTH LOW LINE as a separator for emoji keywords
- Unbreak sqlite on Python 3.6 (thanks to Jan Alexander Steffens)
- Return immediately if _update_candidates() is called with
  empty input (Resolves: rhbz#1413082)

* Tue Jan 10 2017 Mike FABIAN <mfabian@redhat.com> - 1.5.16-1
- update to 1.5.16
- Remove everything following a tab (including the tab) from
  hunspell dictionary lines (Resolves: rhbz#1411659)
- Delete a candidate correctly from the user database even if
  it starts with a prefix to be stripped from tokens (Resolves: rhbz#1411676)
- Trigger emoji lookup when the input starts or ends with '_' or ' '
- Better handling of BackSpace and Delete when reaching the
  ends of the preëdit (Resolves: rhbz#1411688)
- Search for hunspell dictionaries in a list of directories
  (Resolves: https://github.com/mike-fabian/ibus-typing-booster/issues/6)

* Mon Dec 19 2016 Miro Hrončok <mhroncok@redhat.com> - 1.5.15-2
- Rebuild for Python 3.6

* Fri Dec 09 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.15-1
- update to 1.5.15
- Default value for self._show_status_info_in_auxiliary_text should be True
- Don’t use keyword arguments when instantiating IBus.LookupTable()
- Add an option to choose the orientation of the lookup table
- Update translations from zanata (de, pl, and uk updated)
- Update emojione.json

* Fri Nov 25 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.14-1
- update to 1.5.14
- Reopen preëdit not only on Backspace but also on Delete and arrow keys
- Fix "delete whitespace when committing punctuation" problem in firefox
  Resolves rhbz#1399192
- Add pt_BR translations from zanata. Update uk, pl, and de translations from zanata.
- Add an option to show/hide the status information in the auxiliary text
- Use ballot box characters in front of the mode indicators in the auxiliary text

* Mon Nov 21 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.13-1
- update to 1.5.13
- Update French translations from zanata

* Sun Nov 20 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.12-1
- update to 1.5.12
- Display existing shortcuts and make it possible to delete them
- Update translations from zanata (de, pl, uk)

* Thu Nov 17 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.11-1
- update to 1.5.11
- Add feature to define custom shortcuts
- Merge editor and tabengine classes

* Wed Nov 09 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.10-1
- update to 1.5.10
- Make accent insensitive matching also work in the user database
- Add test cases for accent insensitive matching
- Add 'No' (Number, Other) to VALID_CATEGORIES to be able to
  match ¹ U+00B9 SUPERSCRIPT ONE

* Mon Oct 24 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.9-1
- update to 1.5.9
- Make it possible to use a database in different locations than the default
- Clear candidate list as well when clearing the lookup table
- Add missing CLDR xml files to tar ball
- Add unit tests

* Mon Oct 10 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.8-1
- update to 1.5.8
- Pull translations from Zanata (uk and fr updated)
- Match many more Unicode characters in the emoji matcher
- Make it possible to match Unicode characters by typing the hexadecimal code point
- If one tries to set a non-existing input method, don’t crash,
  only print an error in the debug log
- Add key and mouse bindings for “Off the record” mode to README

* Mon Sep 19 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.7-1
- update to 1.5.7
- Pull translations from Zanata (de, pl, uk updated)
- Make the list of characters to auto commit configurable
  (Empty list by default)
- Fix duplicates in the candidate list caused by overwriting
  input_phrase with the NFC version
- Don’t show the special candidates for missing dictionaries for
  Japanese and Chinese
- Implement do_cursor_up() and do_cursor_down() to make scrolling
  the lookup table with the mouse wheel work (Needs also a patch in ibus)
- Add an “Off the record mode” (also gets a property menu)
- Tooltips don’t seem to work on sub-properties, remove the tooltips there
- Add a property menu for the emoji prediction mode
- Make triggering a commit with “Left” or “Control+Left” work
  correctly in “Tab enable mode ” again
- Down, Up, Page_Down, and Page_Up should trigger a commit and
  be passed to the application if possible
- If “☑ Enable suggestions by Tab key” is on make it possible
  to close the lookup table with Escape but keep the preëdit
- If “☑ Enable suggestions by Tab key” is on, don’t autocommit digits
- Make autocommitting much more rare (for characters which are not
  the first typed character)
- Don’t autocommit the first typed character unless absolutely necessary
- Even when “☑ Enable suggestions by Tab key” is used,
  don’t complete empty strings

* Mon Sep 12 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.6-1
- update to 1.5.6
- Reduce the number of characters which cause immediate commits a lot
- Load CLDR data for *all* languages in the _expand_languages() list
- Currency symbols should neither be stripped from tokens nor
  trigger an immediate commit
- Fix bidi reordering problem in the candidate list for
  right-to-left candidates followed by comments
- Update emoji annotations from CLDR (de_CH and sr_Latn new,
  the others updated)
- Remove category 'Pc' from categories to commit immediately
  (allow _ to be typed into the preëdit always)
- Remove button to install pyhunspell from the setup tool
  (python3-enchant is preferred and even required by the Fedora rpm)
- Include more currency symbols and fullwidth symbols
- Add category from UnicodeData.txt to emoji dictionary
  (For better results when looking up related characters)
- Add 'Sc', # Symbol, Currency to VALID_CATEGORIES
  (to make the currency symbols work)
- Add list of valid characters (to include special characters
  manually)
- Add mouse binding Alt+Mouse3 anywhere in the candidate list
  to start the setup tool

* Sat Sep 10 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.5-1
- update to 1.5.5
- Pull translations form Zanata (de, pl, and uk updated because of
  the new “About” tab)
- If “☑ Enable suggestions by Tab key” option is on, any preëdit
  change should hide the lookup table
- Make showing of similar emoji work even if emoji preditions are off
- Display whether emoji predictions are turned on in the auxiliary string
- Add key and mouse bindings to toggle the emoji predictions
  (AltGr+F6 and Control+Mouse3 anywhere in the candidate list)
- Add AltGr+F10 key binding to open the setup tool
- Allow any amount of white space and '_' characters to seperate words
  in an emoji query string
- Add an “About” tab to the setup tool and put links to home page and
  online documentation there.
- Update README with latest key binding and mouse binding documentation

* Thu Sep 08 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.4-1
- update to 1.5.4
- Accent insensitive matching
- Update pl.po from zanata
- Add cache for the suggestions from the hunspell dictionaries
- Make Control+MouseButton1 remove the clicked candidate from
  the user database (was MouseButton2)
- Change key binding for looking up related candidates
  from Alt+F12 to AltGr+F12
- Change label of the emoji option to
  “☑ Unicode symbols and emoji predictions”

* Sat Sep 03 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.3-1
- update to 1.5.3
- Pull translations from Zanata: updates for pl and uk.
- Fix behaviour of the option “Minimum number of chars for completion”

* Fri Sep 02 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.2-1
- update to 1.5.2
- get_supported_imes(self) and def get_current_imes(self) should
  return copies not the lists directly
- Resolves: rhbz#1372660
- Update emojione.json, version from 2016-07-16
- Pull translations from Zanata: Fixes for fr and pl. New: uk
- Changes in itb_emoji.py necessary because of the update of
  the CLDR emoji annotations.
- Update emoji annotations from CLDR (be, bs, cy, eu, gl, zu
  are new, the others updated).
- Shortcut keys which look up related candidates should enable
  the candidate list
- Show ⏳ HOURGLASS WITH FLOWING SAND in the auxiliary text when
  the lookup table is being updated
- Fix bug when committing the preëdit with Space when no
  candidates are available
- Improve the behaviour of the “Tab” key
- Improve the behaviour of the “Escape” key.
- Make mouse clicks in the candidate list behave differently
  depending on the mouse button
- Add hu-rovas-post.mim to hu_HU.conf

* Fri Aug 12 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.1-1
- update to 1.5.1
- If the query string in EmojiMatcher.candidates() is an emoji
  itself, match similar ones (useful when backspacing to an emoji
  to correct it)                          
- Data files should not be stored gzipped in the repository
- Change displayed input method name from “Hunspell” to “Typing Booster”
- Use Zanata to get more translations
- French translations added (100% translated)
- Polish translations added (100% translated)
- Add Recommends: gdouros-symbola-fonts

* Thu Aug 11 2016 Mike FABIAN <mfabian@redhat.com> - 1.5.0-1
- update to 1.5.0
- If the lookup table shows related words, “Escape” shows the
  original lookup table
- Use itb_nltk.py to find related words (synonyms, hypernyms, and hyponyms)
- Add a module to find related words using NLTK
- Add a feature to find similar emoji
- Add predictions for emoji (optional, on by default)
- Add a module to match emoji using Unicode, CLDR, and emojione data
- Make typing-booster.appdata.xml translatable
- When ignoring key release events, “False” should be returned, not “True”
- Resolves: rhbz#1365497
- Make typing smoother by updating the candidates using GLib.idle_add()
- Make it possible to enter a space into the preëdit by
  typing “G- ” (AltGr+Space)

* Sun Jul 17 2016 Mike FABIAN <mfabian@redhat.com> - 1.4.8-1
- update to 1.4.8
- Commit preëdit if modifier keys without transliteration are
  typed and pass the key through
- Resolves: rhbz#1351748 in a better way

* Mon Jul 11 2016 Mike FABIAN <mfabian@redhat.com> - 1.4.7-1
- update to 1.4.7
- Check if the commit key would change the transliteration if
  used as regular input
- Resolves: rhbz#1353672 

* Fri Jul 01 2016 Mike FABIAN <mfabian@redhat.com> - 1.4.6-1
- update to 1.4.6
- Pass modifier key combinations through if there is no possible
  transliteration for that key combination
- Resolves: rhbz#1351748

* Wed May 11 2016 Mike FABIAN <mfabian@redhat.com> - 1.4.5-1
- update to 1.4.5
- Do not colourize the preëdit dark blue, that is unreadable on
  dark backgrounds
- Resolves: rhbz#1335201
- Set the size of the libm17n mconv conversion buffer correctly
- Resolves: rhbz#1335021

* Tue May 10 2016 Mike FABIAN <mfabian@redhat.com> - 1.4.4-1
- update to 1.4.4
- self._current_imes needs to be updated before self.init_transliterators()
- Resolves: rhbz#1334579

* Thu Apr 28 2016 Mike FABIAN <mfabian@redhat.com> - 1.4.3-1
- update to 1.4.3
- Fix AttributeError: 'editor' object has no attribute 'trans'
- Resolves: rhbz#1331338

- update to 1.4.2
- Fix mistyped variable name
- Resolves: rhbz#1330461
- Add option to remember the preëdit input method used last
- Update German translations
- The combobox in the setup tool should show the first supported ime
  from dconf

* Wed Apr 20 2016 Mike FABIAN <mfabian@redhat.com> - 1.4.1-1
- update to 1.4.1
- Avoid unnessary initialization of transliterators when the set
  of input methods has not changed
- Add  property menu to choose the current preedit input method
- Display preëdit input method in aux_string also when number of
  candidates is not shown
- Add some tooltips to the setup tool
- Update German translations

* Sat Apr 09 2016 Mike FABIAN <mfabian@redhat.com> - 1.4.0-3
- update to 1.4.0
- Call IBus.Bus() in __main__, not in __init__ of class SetupUI
- Resolves: rhbz#1325338
- Multilingual support, more than one language in an engine
- Simple option in the setup tool to enable bilingual support
  (i.e. one language + Enlish).
- The default of the option “Add direct input” in the setup tool
  should be false (bug found by Pravin Satpute).
- Changing the main input method with the setup tool should not
  remove the direct input (bug found by Pravin Satpute)
- Add 0 as a digit to commit directly when using digits as select keys
- Clear dictionaries in Hunspell class before reloading

* Mon Feb 08 2016 Mike FABIAN <mfabian@redhat.com> - 1.3.1-1
- update to 1.3.1
- Use new transliterator  from m17n_translit.py also when switching
  input methods in the setup tool
- Resolves: rhbz#1304677

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.3.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Dec 15 2015 Mike FABIAN <mfabian@redhat.com> - 1.3.0-3
- update to 1.3.0
- Use libm17n directly instead of going through libtranslit
- Forward key events triggering a commit using "forward_key_event()"
  instead of relying on "return False"
- Resolves: rhbz#1291238
- Add code to use F1-F9 as well as keys to select candidates
  for commit or remove
- Don not commit invisible candidates with select keys with numbers
  greater than the length of a page of the candidate list
- Control-arrow-left and Control-arrow-right now commit when
  the edges of the preedit string are reached
- Alt-<number> does not delete a prediction anymore,
  now only Control-<number> does this
- Add an option to disable the use of the digits 1-9 as
  selection keys (useful if one wants easier number input,
  selection then works only with the F1-F9 keys)
- Support input methods using AltGr (e.g. mr-inscript2)
  and Alt keys (e.g. ta-lk-renganathan)
- Resolves: rhbz#1051405
- Resolves: rhbz#772665

* Tue Nov 10 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.15-2
- Rebuilt for https://fedoraproject.org/wiki/Changes/python3.5

* Mon Nov 02 2015 Mike FABIAN <mfabian@redhat.com> - 1.2.15-1
- Use open() instead of codecs.open() to make the input method help button work again
- Resolves: rhbz#1276992

* Tue Sep 22 2015 Mike FABIAN <mfabian@redhat.com> - 1.2.14-2
- Fix wrong bug number in changelog
- Resolves: rhbz#1268153

* Tue Sep 22 2015 Mike FABIAN <mfabian@redhat.com> - 1.2.14-1
- Add Catalan translations, thanks to Robert Antoni Buj Gelonch <rbuj@fedoraproject.org>
- Resolves: rhbz#1268153
- Add Catalan engine
- Update German translations
- Add optional debug code
- Fix some pylint warnings

* Tue Sep 22 2015 Mike FABIAN <mfabian@redhat.com> - 1.2.13-1
- Add a property to start the setup tool
- Resolves: rhbz#1260088

* Thu Aug 27 2015 Mike FABIAN <mfabian@redhat.com> - 1.2.12-1
- Use open() instead of codecs.open() to fix dictionary loading problem on F23
- Resolves: rhbz#1257465

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.11-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed Mar 25 2015 Richard Hughes <rhughes@redhat.com> - 1.2.11-2
- Register as an AppStream component.

* Wed Sep 24 2014 Mike FABIAN <mfabian@redhat.com> - 1.2.11-1
- Require Python >= 3.3
- Always write xml output in UTF-8 encoding, not in the encoding of the current locale
- Change class “KeyEvent” to store the keycode as well
- Commit when hitting the borders of the preëdit with the arrow keys (Resolves: rhbz#1140502)

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.10-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon Mar 17 2014 Mike FABIAN <mfabian@redhat.com> - 1.2.10-2
- Resolves: rhbz#1075892 update package URL to typingbooster.org

* Thu Feb 27 2014 Mike FABIAN <mfabian@redhat.com> - 1.2.10-1
- make profiling work again and make it easier to use
- port from Python2 to Python3
- add python-enchant support

* Fri Jan 17 2014 Mike FABIAN <mfabian@redhat.com> - 1.2.9-1
- Fix behaviour of arrow right keys in preëdit (Resolves: rhbz#1049324)
- Add timestamps to entries in the user database
- Add timestamp support to user_transliteration.py
- Use a single user database for all engines
- Add *-inscript2 transliteration options to the Indian languages where these were still missing (Resolves: rhbz#1051405)
- Make it possible to use multiple hunspell dictionaries at the same time
- Make it possible to specify a list of dictionaries in the config files
- Make it possible to get a word back into preëdit by using backspace (Resolves: rhbz#1032442)

* Fri Dec 20 2013 Anish Patil <apatil@redhat.com> - 1.2.8-1
- Change of IME name for oriya language  Resolves: rhbz#1045299
- Fixed issue multiple instances of setup menu Resolves: rhbz#1045294

* Wed Nov 20 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.7-1
- Don’t strip characters with Unicode category “Cf” (Other, format) from tokens (Resolves: rhbz#1032504)

* Thu Nov 14 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.6-1
- Change wording of the option to show the total number of candidates (Resolves: rhbz#1029748)
- Commit candidate clicked on with the mouse (Resolves: rhbz#1029822)
- Use direct input also for IBus.InputPurpose.PIN
- remove unused und superfluous arguments of constructor of Hunspell class
- Add some transliteration options to .conf files which had only native keyboard enabled

* Fri Oct 11 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.5-1
- Add feature to display input method description to setup tool (Resolves: rhbz#1001581)
- Remove the options “m17n_mim_name” and “other_ime” from the .conf files
- remove tab_enable option from config files

* Tue Oct 01 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.4-3
- Resolves: rhbz#1013992 ibus-typing-booster needs to have ibus write-cache --system in %%post and %%postun

* Mon Sep 30 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.4-2
- remove superfluous line break in changelog

* Sat Sep 28 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.4-1
- Use normalization form NFD internally for Korean as well
- Add check for input purpose for gnome-shell password dialog (Resolves: rhbz#1013008 - ibus-typing-booster shows entered text in password fields)

* Mon Sep 16 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.3-3
- remove obsoletes/provides, not needed anymore for Fedora >= 21

* Tue Aug 06 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.3-1
- Update to 1.2.3 upstream version
- Fix exception handling when trying to install a rpm package (Resolves: rhbz#986178)

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.2.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Mon Jul 15 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.2-1
- Update to 1.2.2 upstream version
- Commit immediately when certain punctuation characters are typed and transliteration is not used (Resolves: rhbz#981179)
- Add an option to try completion only when a minimum number of characters has been typed

* Wed Jul 03 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.1-1
- Update to 1.2.1 upstream version
- Pop up a message box when a file has been read to train the database, indicating success or failure (Resolves: rhbz#979933)
- Update German translation
- Ignore most punctuation characters and mathematical symbols when tokenizing (Resolves: rhbz#979939)

* Fri Jun 28 2013 Mike FABIAN <mfabian@redhat.com> - 1.2.0-1
- Update to 1.2.0 upstream version
- Make TAB when used to enable/disable the lookup table work as a toogle
- Create a VIEW for “LIKE input_phrase%%” in select_words() and use that
  in the following SELECT statements (Makes candidate calculation more
  than 10 times faster)

* Mon Jun 24 2013 Mike FABIAN <mfabian@redhat.com> - 1.1.0-1
- Update to 1.1.0 upstream version
- Add a commit=True parameter to check_phrase_and_update_frequency()
- Fix that the page_size is shown as 0 in the setup tool if it has not been set before
- Do not use AUTOINCREMENT
- Make it possible to exit the setup tool by typing Control-C in the terminal
- Add feature to read a text file for training the user database
- Update German translations and .pot file
- Fix error when the hunspell dictionary for an engine is missing

* Tue Jun 18 2013 Mike FABIAN <mfabian@redhat.com> - 1.0.3-1
- Update to 1.0.3 upstream version
- Don’t output page_size in “/usr/libexec/ibus-engine-typing-booster --xml” (Resolves: rhbz#975449 - ibus-daemon prints warnings because “/usr/libexec/ibus-engine-typing-booster --xml” prints the invalid element “page_size”)
- Use ~/.local/share/ibus-typing-booster/ to store user data and log files (Resolves: rhbz#949035 - don't use a hidden directory under .local/share)

* Fri Jun 14 2013 Mike FABIAN <mfabian@redhat.com> - 1.0.2-1
- Update to 1.0.2 upstream version
- Push context *after* writing the trigram to the database

* Fri Jun 14 2013 Mike FABIAN <mfabian@redhat.com> - 1.0.1-1
- Update to 1.0.1 upstream version
- Fix problem when IBUS_TYPING_BOOSTER_DEBUG_LEVEL is not set

* Thu Jun 13 2013 Mike FABIAN <mfabian@redhat.com> - 1.0.0-1
- Update to 1.0.0 upstream version
- Remove mudb and use “Write-Ahead Logging”
- Introduce an environment variable IBUS_TYPING_BOOSTER_DEBUG_LEVEL for debugging
- Speed up converting an old database to the current format
- Make prediction more intelligent by using context of up to 2 previous words
- Automatically remove whitespace between the last word and a punctuation character ending a sentence

* Sun Jun 02 2013 Mike FABIAN <mfabian@redhat.com> - 0.0.32-1
- Update to 0.0.32 upstream version
- Resolves: rhbz#969847 - Editing in the preëdit of ibus-typing-booster behaves weird, especially with transliteration
- Fix behaviour of Control+Number
- When committing by typing TAB, update frequency data in user database
- When committing by tying RETURN or ENTER, update frequency data in user database
- Do not try to match very long words in the hunspell dictionaries
- Rewrite the code for moving and editing within the preëdit (rhbz#969847)
- Fix encoding error when changing values with the setup tool
- Add ko_KR.conf and ko_KR.svg
- Use normalization forms NFD or NFKD internally and NFC externally
- Remove old way of using libtranslit via ctypes
- Get rid of “freq” column in databases
- Remove too simpleminded auto-capitalization

* Wed May 29 2013 Mike FABIAN <mfabian@redhat.com> - 0.0.31-1
- Update to 0.0.31 upstream version
- Resolves: rhbz#968209 - Typing characters which are not explicitly listed as “valid_input_chars” in .conf files in ibus-typing-booster get inserted in a weird position
- Remove lots of unused and/or useless code
- Simplify some code
- Fix the problem that after “page down” the first “arrow down” does not move down in the lookup table
- Never use “-” or “=” as page up and page down keys
- Print more useful debug output when an exception happens
- Replace unencodable characters when asking pyhunspell for suggestions
- Get dictionary encoding from .aff file
- Get rid of the the variable “valid_input_chars” (rhbz#968209)
- Remove option “valid_input_chars” from .conf files and template.txt
- Replace keysym2unichr(key.code) with IBus.keyval_to_unicode(key.code)

* Sun May 26 2013 Mike FABIAN <mfabian@redhat.com> - 0.0.30-1
- Update to 0.0.30 upstream version
- simplify database structure and code
- The Swedish hunspell dictionary is in UTF-8, not ISO-8859-1
- SQL LIKE should behave case sensitively
- Do not throw away the input phrase in hunspell_suggest.suggest()
- Merge candidates which have the same resulting phrase in select_words()
- Remove phrases always from the user database when typing Alt+Number
- Sync memory user database “mudb” to disk user database “user_db” on focus out
- Delete all records from mudb after syncing to user_db
- Do not prevent phrases of length < 4 to be added to the frequency database
- Resolves: #966947 - When typing a/ with the da_DK ibus-typing-booster, one gets weird matches like a/ACJSTVW
- Do not use lang_chars for matching in the hunspell dictionaries, return immediately if input contains a “/” (Resolves: #966947)
- Remove lang_chars variable
- Use re.escape() to escape the string typed by the user correctly for use in a regular expression
- When removing a phrase with Alt+Number, remove it independent of the input_phrase

* Tue May 14 2013 Mike FABIAN <mfabian@redhat.com> - 0.0.29-1
- Update to 0.0.29 upstream version
- Resolves: #962609  - [abrt] ibus-typing-booster-0.0.28-1.fc19: main.py:107:__init__:AttributeError: tabsqlitedb instance has no attribute 'get_ime_property' (Fix setup tool to use the new class for parsing the config files)
- Avoid adding duplicates to the database by checking first whether phrase is already there in add_phrase()

* Fri May 10 2013 Mike FABIAN <mfabian@redhat.com> - 0.0.28-1
- Update to 0.0.28 upstream version
- Resolves: #961923 - python /usr/share/ibus-typing-booster/engine/main.py --xml is extremely slow when many hunspell dictionaries are installed
- Put the input phrase into a single column in the databases instead of using one column for each character
- Get rid of tab_dict

* Mon May 06 2013 Mike FABIAN <mfabian@redhat.com> - 0.0.27-1
- Update to 0.0.27 upstream version
- Resolves: #959860 - [as_IN] Wrong keymap name Assami (fix spelling error in language name for Assamese)
- Resolves: #958770 - [ibus-typing-Booster][gu-IN]- Typo error (fix spelling error in language name for Gujarati)
- Resolves: #875285 - IME names too long in gnome-shell Input Sources indicator (remove ✓ from symbol in the .conf files)
- simplify code in select_words()
- remove some unused functions

* Thu Feb 14 2013 Mike FABIAN <mfabian@redhat.com> - 0.0.26-1
- Update to 0.0.26 upstream version
- Resolves: #910986 - The arrow icons at the bottom of the candidate lookup table of ibus-typing-booster do not work
- Use different .svg icons for all engines
- Increase number of suggestions from hunspell
- Use the auxiliary text to display the number of candidates
- Make the display of the number of candidates in the auxiliary text optional
- Display of the number of candidates needs to be updated on page-up and page-down

* Thu Feb 14 2013 Mike FABIAN <mfabian@redhat.com> - 0.0.25-1
- Update to 0.0.25 upstream version
- Port to use pygobject3

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.24-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Thu Dec 06 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.24-1
- Update to 0.0.24 upstream version
- Resolves: #884808 - ibus-typing-booster should also show candidates which correct spelling errors
- Use pyhunspell to add spell-checking suggestions
- Use underline for preedit
- Colourize spellchecking suggestions and system phrases already used

* Fri Nov 23 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.23-1
- Update to 0.0.23 upstream version
- Resolves: #879261  dictionary is not automatically reloaded when it is installed via the setup tool
- Make the engine reload the dictionary when the dictionary is installed via the setup tool

* Wed Nov 14 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.22-1
- Update to 0.0.22 upstream version
- Resolves: #876666 Properties of ibus-typing-booster to select input methods are not shown by gnome-shell in f18
- Make the engine use the input method from the dconf setting
- Add combobox to setup GUI to select input method
- Update German translation

* Mon Nov 12 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.21-1
- Update to 0.0.21 upstream version
- Resolves: #875285 Shorten symbol displayed in gnome panel
- Add space before ( in long display name

* Thu Nov 08 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.20-1
- Update to 0.0.20 upstream version
- Resolves: #874421
- Improve setup GUI to make correct dictionary installable (Resolves #874421)
- Add page size spin button to setup tool
- Connect signals in __init__ of SetupUI after setting the initial values
- Make the setup tool find the right config file in gnome-shell on Fedora 18
- Update German translation

* Tue Nov 06 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.19-1
- Update to 0.0.19 upstream version
- fix rpmlint warning “incorrect-fsf-address”

* Wed Oct 31 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.18-1
- Update to 0.0.18 upstream version
- Resolves: #871056
- Save setup option “Enable suggestions by Tab Key” correctly in dconf (Resolves: #871056)
- Make setup dialog translatable and add German translations

* Wed Oct 24 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.16-1
- Update to 0.0.16 upstream version
- Resolves: #869687
- Make enabling the lookup table with the TAB key work correctly
- Simplify code in add_input()
- Make German input typed in NFD work

* Mon Oct 22 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.15-1
- Update to 0.0.15 upstream version
- Resolves: #869050
- Make sure the lookup table is hidden if there are no candidates to suggest (#869050)

* Mon Oct 22 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.14-1
- Update to 0.0.14 upstream version
- Show an obvious warning when the hunspell dictionary needed is not found
- Show exact matches in the .dic files as suggestions as well
- Do not forget the input method used last when activating a previously used engine
- Make spelling of the value of “symbol” in the .conf files more consistent
- include the file ru_RU.conf

* Thu Oct 18 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.13-1
- Update to 0.0.13 upstream version, in 0.0.12 I forgot to
  include the file de_DE.conf

* Thu Oct 18 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.12-1
- Update to 0.0.12 upstream version, in 0.0.11 I forgot to
  include the file keysym2ucs.py

* Thu Oct 18 2012 Mike FABIAN <mfabian@redhat.com> - 0.0.11-1
- Upstream has released 0.0.11 version containing the following
  improvements:
- Add .conf files for many languages and improve some existing .conf files
- Read other_ime option case insensitively
- Split only at the first = in a line in a .conf file
- Fix the problem that the user defined phrases are lost when switching engines
- use “layout = default” instead of “layout = us” in all .conf files
- Make sure the input of transliterate() is UTF-8 encoded
- Add a keysym2unichr() function and use it to support languages which have non Latin1 input
- Let first letter start with index 1 in autogenerated tabdict
- Use autogenerated tabdict always, not only in m17n mode
- Use special value 'NoIme' to indicate that no input method should be used
- Use contents of lang_chars for the regexp to match words in the dictionaries
- In process_key_event, do not return False when a non-ASCII character has been typed
- Read option valid_input_chars as UTF-8
- Use the encoding option from the .conf file always, not only in m17n mode
- Whether m17n mode is used should depend on the .conf file, not the language
- Use correct encoding to decode the dictionary file
- Some other minor fixes

* Wed Sep 26 2012 Anish Patil <apatil@redhat.com> - 0.0.10-1
- Upstream has released new version.

* Thu Sep 13 2012 Anish Patil <apatil@redhat.com> - 0.0.9-1
- Upstream has released new version.

* Tue Aug 14 2012 Anish Patil <apatil@redhat.com> - 0.0.8-1
- Upstream has released new version.

* Tue Jul 17 2012 Anish Patil <apatil@redhat.com> - 0.0.7-1
- The first version.
- derieved from ibus-table developed by Yu Yuwei <acevery@gmail.com>
