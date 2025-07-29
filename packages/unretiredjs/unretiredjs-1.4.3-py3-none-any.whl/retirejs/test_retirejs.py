import retirejs as retire
import unittest
import hashlib
from vulnerabilities import definitions

content = "data"
hash = hashlib.sha1(content.encode("utf-8")).hexdigest()


# Some tests might fail because new bugs introduced :(

class TestingFileContentJS(unittest.TestCase):

    def test1(self):
        # Vulnerable version (DOMPurify CVE-2024-48910)
        result = retire.scan_file_content("/*! @license DOMPurify 2.4.0")
        self.assertTrue(retire.is_vulnerable(result))

    def test2(self):
        # Vulnerable version (AngularJS CVE-2023-26117)
        result = retire.scan_file_content("/*\n AngularJS v1.8.2\n (c) 2010-2020 Google LLC. http://angularjs.org\n License: MIT\n*/")
        self.assertTrue(retire.is_vulnerable(result))

    def test3(self):
        # Vulnerable version (jQuery CVE-2019-11358)
        result = retire.scan_file_content("/*! jQuery v1.12.0 asdasd ")
        self.assertTrue(retire.is_vulnerable(result))

    def test4(self):
        # Non-vulnerable version (DOMPurify latest)
        result = retire.scan_file_content("/*! @license DOMPurify 3.2.4")
        self.assertFalse(retire.is_vulnerable(result))

    def test5(self):
        # Vulnerable version (AngularJS CVE-2022-25844)
        result = retire.scan_file_content("/*\n AngularJS v1.8.3\n (c) 2010-2020 Google LLC. http://angularjs.org\n License: MIT\n*/")
        self.assertTrue(retire.is_vulnerable(result))

    def test6(self):
        # Non-vulnerable version (jQuery latest)
        result = retire.scan_file_content("/*! jQuery v3.7.1 asdasd ")
        self.assertFalse(retire.is_vulnerable(result))


class TestingUri(unittest.TestCase):

    def testuri1(self):
        # Vulnerable version (DOMPurify CVE-2024-48910) 
        result = retire.scan_uri(
            "https://cdnjs.cloudflare.com/ajax/libs/dompurify/2.4.0/purify.min.js")
        self.assertFalse(retire.is_vulnerable(result))

    def testuri2(self):
        # Vulnerable version (AngularJS CVE-2023-26117)
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/angularjs/1.8.2/angular.min.js")
        self.assertTrue(retire.is_vulnerable(result))

    def testuri3(self):
        # Vulnerable version (jQuery CVE-2019-11358)
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/1.12.0/jquery.min.js")
        self.assertTrue(retire.is_vulnerable(result))

    def testuri4(self):
        # Non-vulnerable version (DOMPurify latest)
        result = retire.scan_uri(
            "https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.2.4/purify.min.js")
        self.assertFalse(retire.is_vulnerable(result))

    def testuri5(self):
        # Vulnerable version (AngularJS CVE-2022-25844)
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/angularjs/1.8.3/angular.min.js")
        self.assertTrue(retire.is_vulnerable(result))

    def testuri6(self):
        # Non-vulnerable version (jQuery latest)
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js")
        self.assertFalse(retire.is_vulnerable(result))


class TestingHash(unittest.TestCase):

    def testhash1(self):
        # Vulnerable version (CVE-2011-4969)
        definitions["jquery"]["extractors"]["hashes"][hash] = "1.6.1"
        result = retire.scan_file_content(content)
        self.assertTrue(retire.is_vulnerable(result))

    def testhash2(self):
        # Vulnerable version (CVE-2012-6708)
        definitions["jquery"]["extractors"]["hashes"][hash] = "1.8.1"
        result = retire.scan_file_content(content)
        self.assertTrue(retire.is_vulnerable(result))

    def testhash3(self):
        # Vulnerable version (CVE-2019-11358)
        definitions["jquery"]["extractors"]["hashes"][hash] = "1.12.1"
        result = retire.scan_file_content(content)
        self.assertTrue(retire.is_vulnerable(result))

    def testhash4(self):
        # Non-vulnerable version (latest 3.7.1)
        definitions["jquery"]["extractors"]["hashes"][hash] = "3.7.1"
        result = retire.scan_file_content(content)
        self.assertFalse(retire.is_vulnerable(result))

    def testhash5(self):
        # Non-vulnerable version (3.6.0+)
        definitions["jquery"]["extractors"]["hashes"][hash] = "3.6.0"
        result = retire.scan_file_content(content)
        self.assertFalse(retire.is_vulnerable(result))

    def testhash6(self):
        # Non-vulnerable version (3.5.0+)
        definitions["jquery"]["extractors"]["hashes"][hash] = "3.5.0"
        result = retire.scan_file_content(content)
        self.assertFalse(retire.is_vulnerable(result))


class TestingFilename(unittest.TestCase):

    def testfilename1(self):
        # Vulnerable version (DOMPurify CVE-2024-48910)
        result = retire.scan_filename("purify-2.4.0.js")
        self.assertFalse(retire.is_vulnerable(result))

    def testfilename2(self):
        # Vulnerable version (AngularJS CVE-2023-26117)
        result = retire.scan_filename("angular-1.8.2.js")
        self.assertTrue(retire.is_vulnerable(result))

    def testfilename3(self):
        # Vulnerable version (jQuery CVE-2019-11358)
        result = retire.scan_filename("jquery-1.12.0.js")
        self.assertTrue(retire.is_vulnerable(result))

    def testfilename4(self):
        # Non-vulnerable version (DOMPurify latest)
        result = retire.scan_filename("purify-3.2.4.js")
        self.assertFalse(retire.is_vulnerable(result))

    def testfilename5(self):
        # Vulnerable version (AngularJS CVE-2022-25844)
        result = retire.scan_filename("angular-1.8.3.js")
        self.assertTrue(retire.is_vulnerable(result))

    def testfilename6(self):
        # Non-vulnerable version (jQuery latest)
        result = retire.scan_filename("jquery-3.7.1.js")
        self.assertFalse(retire.is_vulnerable(result))


class TestingVersion(unittest.TestCase):

    def testVersion1(self):
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/10.0.0.beta.3/jquery.min.js")
        self.assertFalse(retire.is_vulnerable(result))

    def testVersion2(self):
        definitions["jquery"]["vulnerabilities"].append(
            {"atOrAbove": "10.0.0-*", "below": "10.0.1"})
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/10.0.0.beta.2/jquery.min.js",
            definitions)
        self.assertTrue(retire.is_vulnerable(result))

    def testVersion3(self):
        definitions["jquery"]["vulnerabilities"] = [{"below": "10.0.0.beta.2"}]
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/10.0.0.beta.3/jquery.min.js",
            definitions)
        self.assertFalse(retire.is_vulnerable(result))

    def testVersion4(self):
        definitions["jquery"]["vulnerabilities"] = [{"below": "1.9.0b1"}]
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/1.9.0rc1/jquery.min.js", definitions)
        self.assertFalse(retire.is_vulnerable(result))

    def testVersion5(self):
        definitions["jquery"]["vulnerabilities"] = [{"below": "10.0.0.beta.2"}]
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/10.0.0.beta.2/jquery.min.js",
            definitions)
        self.assertFalse(retire.is_vulnerable(result))

    def testVersion6(self):
        definitions["jquery"]["vulnerabilities"] = [{"below": "10.0.0.beta.2"}]
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/10.0.0.beta.1/jquery.min.js",
            definitions)
        self.assertTrue(retire.is_vulnerable(result))

    def testVersion7(self):
        definitions["jquery"]["vulnerabilities"] = [{"below": "10.0.0"}]
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/10.0.0.beta.1/jquery.min.js",
            definitions)
        self.assertTrue(retire.is_vulnerable(result))

    def testVersion8(self):
        definitions["jquery"]["vulnerabilities"] = [{"below": "10.0.0"}]
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/10.0.0.rc.1/jquery.min.js", definitions)
        self.assertTrue(retire.is_vulnerable(result))

    def testVersion9(self):
        definitions["jquery"]["vulnerabilities"] = [{"below": "10.0.0.beta.2"}]
        result = retire.scan_uri(
            "https://ajax.googleapis.com/ajax/libs/jquery/10.0.0.rc.1/jquery.min.js", definitions)
        self.assertFalse(retire.is_vulnerable(result))


if __name__ == '__main__':
    unittest.main()
