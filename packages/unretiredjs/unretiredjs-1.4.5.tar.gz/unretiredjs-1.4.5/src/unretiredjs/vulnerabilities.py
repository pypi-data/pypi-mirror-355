definitions = {
    "@angular/core": {
        "extractors": {
            "func": [
                "document.querySelector('[ng-version]').getAttribute('ng-version')",
                "window.getAllAngularRootElements()[0].getAttribute(['ng-version'])"
            ]
        },
        "vulnerabilities": [
            {
                "atOrAbove": "0",
                "below": "10.2.5",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-4231"
                    ],
                    "githubID": "GHSA-c75v-2vq8-878f",
                    "summary": "Cross site scripting in Angular"
                },
                "info": [
                    "https://github.com/advisories/GHSA-c75v-2vq8-878f",
                    "https://github.com/angular/angular",
                    "https://github.com/angular/angular/commit/0aa220bc0000fc4d1651ec388975bbf5baa1da36",
                    "https://github.com/angular/angular/commit/47d9b6d72dab9d60c96bc1c3604219f6385649ea",
                    "https://github.com/angular/angular/commit/ba8da742e3b243e8f43d4c63aa842b44e14f2b09",
                    "https://github.com/angular/angular/issues/40136",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-4231",
                    "https://security.snyk.io/vuln/SNYK-JS-ANGULARCORE-1070902",
                    "https://vuldb.com/?id.181356"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "11.0.0",
                "below": "11.0.5",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-4231"
                    ],
                    "githubID": "GHSA-c75v-2vq8-878f",
                    "summary": "Cross site scripting in Angular"
                },
                "info": [
                    "https://github.com/advisories/GHSA-c75v-2vq8-878f",
                    "https://github.com/angular/angular",
                    "https://github.com/angular/angular/commit/0aa220bc0000fc4d1651ec388975bbf5baa1da36",
                    "https://github.com/angular/angular/commit/47d9b6d72dab9d60c96bc1c3604219f6385649ea",
                    "https://github.com/angular/angular/commit/ba8da742e3b243e8f43d4c63aa842b44e14f2b09",
                    "https://github.com/angular/angular/issues/40136",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-4231",
                    "https://security.snyk.io/vuln/SNYK-JS-ANGULARCORE-1070902",
                    "https://vuldb.com/?id.181356"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "11.1.0-next.0",
                "below": "11.1.0-next.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-4231"
                    ],
                    "githubID": "GHSA-c75v-2vq8-878f",
                    "summary": "Cross site scripting in Angular"
                },
                "info": [
                    "https://github.com/advisories/GHSA-c75v-2vq8-878f",
                    "https://github.com/angular/angular",
                    "https://github.com/angular/angular/commit/0aa220bc0000fc4d1651ec388975bbf5baa1da36",
                    "https://github.com/angular/angular/commit/47d9b6d72dab9d60c96bc1c3604219f6385649ea",
                    "https://github.com/angular/angular/commit/ba8da742e3b243e8f43d4c63aa842b44e14f2b09",
                    "https://github.com/angular/angular/issues/40136",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-4231",
                    "https://security.snyk.io/vuln/SNYK-JS-ANGULARCORE-1070902",
                    "https://vuldb.com/?id.181356"
                ],
                "severity": "medium"
            }
        ]
    },
    "AlaSQL": {
        "extractors": {
            "filecontent": [
                "/\\*!?[ \n]*AlaSQL v([0-9][0-9.a-z_-]+)"
            ],
            "filename": [
                "alasql-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "alasql && alasql.version"
            ],
            "uri": [
                "/alasql[/@]([0-9][0-9.a-z_-]+)/.*\\.js"
            ]
        },
        "npmname": "alasql",
        "vulnerabilities": [
            {
                "below": "0.7.0",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "bug": "SNYK-JS-ALASQL-1082932",
                    "summary": "An arbitrary code execution exists as AlaSQL doesn't sanitize input when characters are placed between square brackets [] or preceded with a backtik (accent grave) ` character. Versions older that 0.7.0 were deprecated in March of 2021 and should no longer be used."
                },
                "info": [
                    "https://security.snyk.io/vuln/SNYK-JS-ALASQL-1082932"
                ],
                "severity": "high"
            }
        ]
    },
    "DOMPurify": {
        "bowername": [
            "DOMPurify",
            "dompurify"
        ],
        "extractors": {
            "filecontent": [
                "/\\*! @license DOMPurify ([0-9][0-9.a-z_-]+)",
                "DOMPurify.version = '([0-9][0-9.a-z_-]+)';",
                "DOMPurify.version=\"([0-9][0-9.a-z_-]+)\"",
                "DOMPurify=.[^\\r\\n]{10,850}?\\.version=\"([0-9][0-9.a-z_-]+)\"",
                "var .=\"dompurify\"+.{10,550}?\\.version=\"([0-9][0-9.a-z_-]+)\""
            ],
            "func": [
                "DOMPurify.version"
            ],
            "hashes": {}
        },
        "npmname": "dompurify",
        "vulnerabilities": [
            {
                "below": "0.6.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "24"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases/tag/0.6.1"
                ],
                "severity": "medium"
            },
            {
                "below": "0.8.6",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "25"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases/tag/0.8.6"
                ],
                "severity": "medium"
            },
            {
                "below": "0.8.9",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "26",
                    "summary": "safari UXSS"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases/tag/0.8.9",
                    "https://lists.ruhr-uni-bochum.de/pipermail/dompurify-security/2017-May/000006.html"
                ],
                "severity": "low"
            },
            {
                "below": "0.9.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "27",
                    "summary": "safari UXSS"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases/tag/0.9.0"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "0",
                "below": "1.0.11",
                "cwe": [
                    "CWE-601"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-25155"
                    ],
                    "githubID": "GHSA-8hgg-xxm5-3873",
                    "summary": "DOMPurify Open Redirect vulnerability"
                },
                "info": [
                    "https://github.com/advisories/GHSA-8hgg-xxm5-3873",
                    "https://github.com/cure53/DOMPurify",
                    "https://github.com/cure53/DOMPurify/commit/7601c33a57e029cce51d910eda5179a3f1b51c83",
                    "https://github.com/cure53/DOMPurify/compare/1.0.10...1.0.11",
                    "https://github.com/cure53/DOMPurify/pull/337",
                    "https://nvd.nist.gov/vuln/detail/CVE-2019-25155"
                ],
                "severity": "medium"
            },
            {
                "below": "2.0.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-16728"
                    ],
                    "githubID": "GHSA-chqj-j4fh-rw7m",
                    "summary": "Fixed an mXSS-based bypass caused by nested forms inside MathML"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases"
                ],
                "severity": "medium"
            },
            {
                "below": "2.0.7",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-mjjq-c88q-qhr6",
                    "summary": "possible to bypass the package sanitization through Mutation XSS"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases"
                ],
                "severity": "high"
            },
            {
                "below": "2.0.16",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "28",
                    "summary": "Fixed an mXSS-based bypass caused by nested forms inside MathML"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases"
                ],
                "severity": "low"
            },
            {
                "below": "2.0.17",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-26870"
                    ],
                    "githubID": "GHSA-63q7-h895-m982",
                    "retid": "29",
                    "summary": "Fixed another bypass causing mXSS by using MathML"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases"
                ],
                "severity": "medium"
            },
            {
                "below": "2.1.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "30",
                    "summary": "Fixed several possible mXSS patterns, thanks @hackvertor"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases"
                ],
                "severity": "low"
            },
            {
                "below": "2.2.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "31",
                    "summary": "Fix a possible XSS in Chrome that is hidden behind #enable-experimental-web-platform-features"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases"
                ],
                "severity": "low"
            },
            {
                "below": "2.2.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "32",
                    "summary": "Fixed an mXSS bypass dropped on us publicly via"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases"
                ],
                "severity": "low"
            },
            {
                "below": "2.2.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "33",
                    "summary": "Fixed an mXSS issue reported"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases"
                ],
                "severity": "low"
            },
            {
                "below": "2.2.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "34",
                    "summary": "Fixed a new MathML-based bypass submitted by PewGrand. Fixed a new SVG-related bypass submitted by SecurityMB"
                },
                "info": [
                    "https://github.com/cure53/DOMPurify/releases"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "0",
                "below": "2.4.2",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-48910"
                    ],
                    "githubID": "GHSA-p3vf-v8qc-cwcr",
                    "summary": "DOMPurify vulnerable to tampering by prototype polution"
                },
                "info": [
                    "https://github.com/advisories/GHSA-p3vf-v8qc-cwcr",
                    "https://github.com/cure53/DOMPurify",
                    "https://github.com/cure53/DOMPurify/commit/d1dd0374caef2b4c56c3bd09fe1988c3479166dc",
                    "https://github.com/cure53/DOMPurify/security/advisories/GHSA-p3vf-v8qc-cwcr",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-48910"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0",
                "below": "2.5.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-47875"
                    ],
                    "githubID": "GHSA-gx9m-whjm-85jf",
                    "summary": "DOMpurify has a nesting-based mXSS"
                },
                "info": [
                    "https://github.com/advisories/GHSA-gx9m-whjm-85jf",
                    "https://github.com/cure53/DOMPurify",
                    "https://github.com/cure53/DOMPurify/blob/0ef5e537a514f904b6aa1d7ad9e749e365d7185f/test/test-suite.js#L2098",
                    "https://github.com/cure53/DOMPurify/commit/0ef5e537a514f904b6aa1d7ad9e749e365d7185f",
                    "https://github.com/cure53/DOMPurify/commit/6ea80cd8b47640c20f2f230c7920b1f4ce4fdf7a",
                    "https://github.com/cure53/DOMPurify/security/advisories/GHSA-gx9m-whjm-85jf",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-47875"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0",
                "below": "2.5.4",
                "cwe": [
                    "CWE-1321",
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-45801"
                    ],
                    "githubID": "GHSA-mmhx-hmjr-r674",
                    "summary": "DOMPurify allows tampering by prototype pollution"
                },
                "info": [
                    "https://github.com/advisories/GHSA-mmhx-hmjr-r674",
                    "https://github.com/cure53/DOMPurify",
                    "https://github.com/cure53/DOMPurify/commit/1e520262bf4c66b5efda49e2316d6d1246ca7b21",
                    "https://github.com/cure53/DOMPurify/commit/26e1d69ca7f769f5c558619d644d90dd8bf26ebc",
                    "https://github.com/cure53/DOMPurify/security/advisories/GHSA-mmhx-hmjr-r674",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-45801"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "3.0.0",
                "below": "3.1.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-47875"
                    ],
                    "githubID": "GHSA-gx9m-whjm-85jf",
                    "summary": "DOMpurify has a nesting-based mXSS"
                },
                "info": [
                    "https://github.com/advisories/GHSA-gx9m-whjm-85jf",
                    "https://github.com/cure53/DOMPurify",
                    "https://github.com/cure53/DOMPurify/blob/0ef5e537a514f904b6aa1d7ad9e749e365d7185f/test/test-suite.js#L2098",
                    "https://github.com/cure53/DOMPurify/commit/0ef5e537a514f904b6aa1d7ad9e749e365d7185f",
                    "https://github.com/cure53/DOMPurify/commit/6ea80cd8b47640c20f2f230c7920b1f4ce4fdf7a",
                    "https://github.com/cure53/DOMPurify/security/advisories/GHSA-gx9m-whjm-85jf",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-47875"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "3.0.0",
                "below": "3.1.3",
                "cwe": [
                    "CWE-1321",
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-45801"
                    ],
                    "githubID": "GHSA-mmhx-hmjr-r674",
                    "summary": "DOMPurify allows tampering by prototype pollution"
                },
                "info": [
                    "https://github.com/advisories/GHSA-mmhx-hmjr-r674",
                    "https://github.com/cure53/DOMPurify",
                    "https://github.com/cure53/DOMPurify/commit/1e520262bf4c66b5efda49e2316d6d1246ca7b21",
                    "https://github.com/cure53/DOMPurify/commit/26e1d69ca7f769f5c558619d644d90dd8bf26ebc",
                    "https://github.com/cure53/DOMPurify/security/advisories/GHSA-mmhx-hmjr-r674",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-45801"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0",
                "below": "3.2.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-26791"
                    ],
                    "githubID": "GHSA-vhxf-7vqr-mrjg",
                    "summary": "DOMPurify allows Cross-site Scripting (XSS)"
                },
                "info": [
                    "https://ensy.zip/posts/dompurify-323-bypass",
                    "https://github.com/advisories/GHSA-vhxf-7vqr-mrjg",
                    "https://github.com/cure53/DOMPurify",
                    "https://github.com/cure53/DOMPurify/commit/d18ffcb554e0001748865da03ac75dd7829f0f02",
                    "https://github.com/cure53/DOMPurify/releases/tag/3.2.4",
                    "https://nsysean.github.io/posts/dompurify-323-bypass",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-26791"
                ],
                "severity": "medium"
            }
        ]
    },
    "DWR": {
        "extractors": {
            "filecontent": [
                " dwr-([0-9][0-9.a-z_-]+).jar"
            ],
            "func": [
                "dwr.version"
            ]
        },
        "npmname": "dwr",
        "vulnerabilities": [
            {
                "below": "1.1.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2007-01-09"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2014-5326/"
                ],
                "severity": "high"
            },
            {
                "below": "2.0.11",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-5325",
                        "CVE-2014-5326"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2014-5326/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3",
                "below": "3.0.RC3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-5325",
                        "CVE-2014-5326"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2014-5326/"
                ],
                "severity": "medium"
            }
        ]
    },
    "ExtJS": {
        "extractors": {
            "filecontent": [
                "/*!\n * Ext JS Library ([0-9][0-9.a-z_-]+)",
                "Ext = \\{[\\s]*/\\*[^/]+/[\\s]*version *: *['\"]([0-9][0-9.a-z_-]+)['\"]",
                "var version *= *['\"]([0-9][0-9.a-z_-]+)['\"], *Version;[\\s]*Ext.Version *= *Version *= *Ext.extend"
            ],
            "filename": [
                "/ext-all-([0-9][0-9.a-z_-]+)(\\.min)?\\.js",
                "/ext-all-debug-([0-9][0-9.a-z_-]+)(\\.min)?\\.js",
                "/ext-base-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "Ext && Ext.versions && Ext.versions.extjs.version",
                "Ext && Ext.version"
            ],
            "uri": [
                "/extjs/([0-9][0-9.a-z_-]+)/.*\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "atOrAbove": "3.0.0",
                "below": "4.0.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-4207",
                        "CVE-2012-5881"
                    ],
                    "summary": "XSS vulnerability in ExtJS charts.swf"
                },
                "info": [
                    "https://typo3.org/security/advisory/typo3-core-sa-2014-001/",
                    "https://www.acunetix.com/vulnerabilities/web/extjs-charts-swf-cross-site-scripting",
                    "https://www.akawebdesign.com/2018/08/14/should-js-frameworks-prevent-xss/"
                ],
                "severity": "medium"
            },
            {
                "below": "6.0.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2007-2285"
                    ],
                    "summary": "Directory traversal and arbitrary file read"
                },
                "info": [
                    "https://packetstormsecurity.com/files/132052/extjs-Arbitrary-File-Read.html",
                    "https://www.akawebdesign.com/2018/08/14/should-js-frameworks-prevent-xss/",
                    "https://www.cvedetails.com/cve/CVE-2007-2285/"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "6.6.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-8046"
                    ],
                    "summary": "XSS in Sencha Ext JS 4 to 6 via getTip() method of Action Columns"
                },
                "info": [
                    "http://seclists.org/fulldisclosure/2018/Jul/8",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-8046"
                ],
                "severity": "medium"
            }
        ]
    },
    "YUI": {
        "bowername": [
            "yui",
            "yui3"
        ],
        "extractors": {
            "filecontent": [
                "/*\nYUI ([0-9][0-9.a-z_-]+)",
                "/yui/license.(?:html|txt)\nversion: ([0-9][0-9.a-z_-]+)"
            ],
            "filename": [
                "yui-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "YUI.Version",
                "YAHOO.VERSION"
            ],
            "hashes": {}
        },
        "npmname": "yui",
        "vulnerabilities": [
            {
                "atOrAbove": "2.4.0",
                "below": "2.8.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-4207"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2010-4207/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "2.5.0",
                "below": "2.8.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-4208"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2010-4208/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "2.8.0",
                "below": "2.8.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-4209"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2010-4209/"
                ],
                "severity": "medium"
            },
            {
                "below": "2.9.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-4710"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2010-4710/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "2.4.0",
                "below": "2.9.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2012-5881"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2012-5881/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "2.5.0",
                "below": "2.9.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2012-5882"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2012-5882/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "2.8.0",
                "below": "2.9.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2012-5883"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2012-5883/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.2.0",
                "below": "3.9.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4941"
                    ],
                    "githubID": "GHSA-64r3-582j-frqm"
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2013-4941/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.2.0",
                "below": "3.9.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4942"
                    ],
                    "githubID": "GHSA-9ww8-j8j2-3788"
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2013-4942/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.0.0",
                "below": "3.10.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4939"
                    ],
                    "githubID": "GHSA-mj87-8xf8-fp4w"
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2013-4939/",
                    "https://clarle.github.io/yui3/support/20130515-vulnerability/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.0.0",
                "below": "3.10.11",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4940"
                    ],
                    "githubID": "GHSA-x5hj-47vv-53p8"
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2013-4940/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.10.12",
                "below": "3.10.13",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4940"
                    ],
                    "githubID": "GHSA-x5hj-47vv-53p8"
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2013-4940/"
                ],
                "severity": "medium"
            }
        ]
    },
    "angularjs": {
        "bowername": [
            "angular.js",
            "angularjs"
        ],
        "extractors": {
            "filecontent": [
                "/\\*[\\*\\s]+(?:@license )?AngularJS v([0-9][0-9.a-z_-]+)",
                "http://errors\\.angularjs\\.org/([0-9][0-9.a-z_-]+)/"
            ],
            "filename": [
                "angular(?:js)?-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "angular.version.full"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/angular(\\.min)?\\.js"
            ]
        },
        "npmname": "angular",
        "vulnerabilities": [
            {
                "atOrAbove": "1.0.0",
                "below": "1.2.30",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "50",
                    "summary": "The attribute usemap can be used as a security exploit"
                },
                "info": [
                    "https://github.com/angular/angular.js/blob/master/CHANGELOG.md#1230-patronal-resurrection-2016-07-21"
                ],
                "severity": "medium"
            },
            {
                "below": "1.5.0-beta.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-14863"
                    ],
                    "githubID": "GHSA-r5fx-8r73-v86c",
                    "summary": "XSS through xlink:href attributes"
                },
                "info": [
                    "https://github.com/advisories/GHSA-r5fx-8r73-v86c",
                    "https://github.com/angular/angular.js/blob/master/CHANGELOG.md#150-beta1-dense-dispersion-2015-09-29"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.3.0",
                "below": "1.5.0-rc2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "49",
                    "summary": "The attribute usemap can be used as a security exploit"
                },
                "info": [
                    "https://github.com/angular/angular.js/blob/master/CHANGELOG.md#1230-patronal-resurrection-2016-07-21"
                ],
                "severity": "medium"
            },
            {
                "below": "1.6.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-28hp-fgcr-2r4h",
                    "summary": "Cross-Site Scripting via JSONP"
                },
                "info": [
                    "https://github.com/advisories/GHSA-28hp-fgcr-2r4h"
                ],
                "severity": "medium"
            },
            {
                "below": "1.6.3",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "retid": "52",
                    "summary": "DOS in $sanitize"
                },
                "info": [
                    "https://github.com/angular/angular.js/blob/master/CHANGELOG.md",
                    "https://github.com/angular/angular.js/pull/15699"
                ],
                "severity": "medium"
            },
            {
                "below": "1.6.3",
                "cwe": [
                    "CWE-942"
                ],
                "identifiers": {
                    "retid": "51",
                    "summary": "Universal CSP bypass via add-on in Firefox"
                },
                "info": [
                    "http://pastebin.com/raw/kGrdaypP",
                    "https://github.com/mozilla/addons-linter/issues/1000#issuecomment-282083435"
                ],
                "severity": "medium"
            },
            {
                "below": "1.6.5",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "53",
                    "summary": "XSS in $sanitize in Safari/Firefox"
                },
                "info": [
                    "https://github.com/angular/angular.js/commit/8f31f1ff43b673a24f84422d5c13d6312b2c4d94"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.5.0",
                "below": "1.6.9",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "48",
                    "summary": "XSS through SVG if enableSvg is set"
                },
                "info": [
                    "https://github.com/angular/angular.js/blob/master/CHANGELOG.md#169-fiery-basilisk-2018-02-02",
                    "https://vulnerabledoma.in/ngSanitize1.6.8_bypass.html"
                ],
                "severity": "low"
            },
            {
                "below": "1.7.9",
                "cwe": [
                    "CWE-1321",
                    "CWE-20",
                    "CWE-915"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-10768"
                    ],
                    "githubID": "GHSA-89mq-4x47-5v83",
                    "retid": "47",
                    "summary": "Prototype pollution"
                },
                "info": [
                    "https://github.com/angular/angular.js/blob/master/CHANGELOG.md#179-pollution-eradication-2019-11-19",
                    "https://github.com/angular/angular.js/commit/726f49dcf6c23106ddaf5cfd5e2e592841db743a"
                ],
                "severity": "high"
            },
            {
                "below": "1.8.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-5cp4-xmrw-59wf",
                    "summary": "XSS via JQLite DOM manipulation functions in AngularJS"
                },
                "info": [
                    "https://github.com/advisories/GHSA-5cp4-xmrw-59wf"
                ],
                "severity": "medium"
            },
            {
                "below": "1.8.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-7676"
                    ],
                    "githubID": "GHSA-mhp6-pxh8-r675",
                    "summary": "XSS may be triggered in AngularJS applications that sanitize user-controlled HTML snippets before passing them to JQLite methods like JQLite.prepend, JQLite.after, JQLite.append, JQLite.replaceWith, JQLite.append, new JQLite and angular.element."
                },
                "info": [
                    "https://github.com/advisories/GHSA-5cp4-xmrw-59wf",
                    "https://nvd.nist.gov/vuln/detail/CVE-2020-7676"
                ],
                "severity": "medium"
            },
            {
                "below": "1.8.4",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-26117"
                    ],
                    "githubID": "GHSA-2qqx-w9hr-q5gx",
                    "summary": "angular vulnerable to regular expression denial of service via the $resource service"
                },
                "info": [
                    "https://github.com/advisories/GHSA-2qqx-w9hr-q5gx"
                ],
                "severity": "medium"
            },
            {
                "below": "1.8.4",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-26116"
                    ],
                    "githubID": "GHSA-2vrf-hf26-jrp5",
                    "summary": "angular vulnerable to regular expression denial of service via the angular.copy() utility"
                },
                "info": [
                    "https://github.com/advisories/GHSA-2vrf-hf26-jrp5"
                ],
                "severity": "medium"
            },
            {
                "below": "1.8.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-25869"
                    ],
                    "githubID": "GHSA-prc3-vjfx-vhm9",
                    "summary": "Angular (deprecated package) Cross-site Scripting"
                },
                "info": [
                    "https://github.com/advisories/GHSA-prc3-vjfx-vhm9"
                ],
                "severity": "medium"
            },
            {
                "below": "1.8.4",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-26118"
                    ],
                    "githubID": "GHSA-qwqh-hm9m-p5hr",
                    "summary": "angular vulnerable to regular expression denial of service via the <input type=\"url\"> element"
                },
                "info": [
                    "https://github.com/advisories/GHSA-qwqh-hm9m-p5hr"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "1.8.4",
                "cwe": [
                    "CWE-791"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-0716"
                    ],
                    "githubID": "GHSA-j58c-ww9w-pwp5",
                    "summary": "AngularJS improperly sanitizes SVG elements"
                },
                "info": [
                    "https://codepen.io/herodevs/pen/qEWQmpd/a86a0d29310e12c7a3756768e6c7b915",
                    "https://github.com/advisories/GHSA-j58c-ww9w-pwp5",
                    "https://github.com/angular/angular.js",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-0716",
                    "https://www.herodevs.com/vulnerability-directory/cve-2025-0716"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "0",
                "below": "1.8.4",
                "cwe": [
                    "CWE-791"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-8373"
                    ],
                    "githubID": "GHSA-mqm9-c95h-x2p6",
                    "summary": "AngularJS allows attackers to bypass common image source restrictions"
                },
                "info": [
                    "https://codepen.io/herodevs/full/bGPQgMp/8da9ce87e99403ee13a295c305ebfa0b",
                    "https://github.com/advisories/GHSA-mqm9-c95h-x2p6",
                    "https://github.com/angular/angular.js",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-8373",
                    "https://www.herodevs.com/vulnerability-directory/cve-2024-8373"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.3.0",
                "below": "1.8.4",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-21490"
                    ],
                    "githubID": "GHSA-4w4v-5hc9-xrr2",
                    "summary": "angular vulnerable to super-linear runtime due to backtracking"
                },
                "info": [
                    "https://github.com/advisories/GHSA-4w4v-5hc9-xrr2",
                    "https://github.com/angular/angular.js",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-21490",
                    "https://security.snyk.io/vuln/SNYK-JAVA-ORGWEBJARSBOWER-6241746",
                    "https://security.snyk.io/vuln/SNYK-JAVA-ORGWEBJARSNPM-6241747",
                    "https://security.snyk.io/vuln/SNYK-JS-ANGULAR-6091113",
                    "https://stackblitz.com/edit/angularjs-vulnerability-ng-srcset-redos"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.3.0-rc.4",
                "below": "1.8.4",
                "cwe": [
                    "CWE-1289"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-8372"
                    ],
                    "githubID": "GHSA-m9gf-397r-hwpg",
                    "summary": "AngularJS allows attackers to bypass common image source restrictions"
                },
                "info": [
                    "https://codepen.io/herodevs/full/xxoQRNL/0072e627abe03e9cda373bc75b4c1017",
                    "https://github.com/advisories/GHSA-m9gf-397r-hwpg",
                    "https://github.com/angular/angular.js",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-8372",
                    "https://www.herodevs.com/vulnerability-directory/cve-2024-8372"
                ],
                "severity": "low"
            },
            {
                "below": "1.999",
                "cwe": [
                    "CWE-1104"
                ],
                "identifiers": {
                    "retid": "54",
                    "summary": "End-of-Life: Long term support for AngularJS has been discontinued as of December 31, 2021"
                },
                "info": [
                    "https://docs.angularjs.org/misc/version-support-status"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.7.0",
                "below": "999",
                "cwe": [
                    "CWE-1333",
                    "CWE-770"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-25844"
                    ],
                    "githubID": "GHSA-m2h2-264f-f486",
                    "summary": "angular vulnerable to regular expression denial of service (ReDoS)"
                },
                "info": [
                    "https://github.com/advisories/GHSA-m2h2-264f-f486"
                ],
                "severity": "medium"
            }
        ]
    },
    "axios": {
        "extractors": {
            "filecontent": [
                "// Axios v([0-9][0-9.a-z_-]+) C",
                "/\\*!? *[Aa]xios v([0-9][0-9.a-z_-]+) ",
                "\\\"axios\\\",\\\"version\\\":\\\"([0-9][0-9.a-z_-]+)\\\"",
                "return\"\\[Axios v([0-9][0-9.a-z_-]+)\\] Transitional"
            ],
            "filename": [
                "axios-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "axios && axios.VERSION"
            ],
            "uri": [
                "/axios/([0-9][0-9.a-z_-]+)/.*\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "0.18.1",
                "cwe": [
                    "CWE-20",
                    "CWE-755"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-10742"
                    ],
                    "githubID": "GHSA-42xw-2xvc-qx8m",
                    "summary": "Axios up to and including 0.18.0 allows attackers to cause a denial of service (application crash) by continuing to accepting content after maxContentLength is exceeded"
                },
                "info": [
                    "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2019-10742",
                    "https://security.snyk.io/vuln/SNYK-JS-AXIOS-174505"
                ],
                "severity": "high"
            },
            {
                "below": "0.21.1",
                "cwe": [
                    "CWE-918"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-28168"
                    ],
                    "githubID": "GHSA-4w2v-q235-vp99",
                    "summary": "Axios NPM package 0.21.0 contains a Server-Side Request Forgery (SSRF) vulnerability"
                },
                "info": [
                    "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-28168",
                    "https://security.snyk.io/vuln/SNYK-JS-AXIOS-1038255"
                ],
                "severity": "medium"
            },
            {
                "below": "0.21.3",
                "cwe": [
                    "CWE-1333",
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-3749"
                    ],
                    "githubID": "GHSA-cph5-m8f7-6c5x",
                    "summary": "Axios is vulnerable to Inefficient Regular Expression Complexity"
                },
                "info": [
                    "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-3749",
                    "https://security.snyk.io/vuln/SNYK-JS-AXIOS-1579269"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0.8.1",
                "below": "0.28.0",
                "cwe": [
                    "CWE-352"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-45857"
                    ],
                    "githubID": "GHSA-wf5p-g6vw-rhxx",
                    "summary": "Axios Cross-Site Request Forgery Vulnerability"
                },
                "info": [
                    "https://github.com/advisories/GHSA-wf5p-g6vw-rhxx",
                    "https://github.com/axios/axios/commit/96ee232bd3ee4de2e657333d4d2191cd389e14d0",
                    "https://github.com/axios/axios/issues/6006",
                    "https://github.com/axios/axios/issues/6022",
                    "https://github.com/axios/axios/pull/6028",
                    "https://github.com/axios/axios/releases/tag/v1.6.0",
                    "https://nvd.nist.gov/vuln/detail/CVE-2023-45857",
                    "https://security.snyk.io/vuln/SNYK-JS-AXIOS-6032459"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "0.30.0",
                "cwe": [
                    "CWE-918"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-27152"
                    ],
                    "githubID": "GHSA-jr5f-v2jv-69x6",
                    "summary": "axios Requests Vulnerable To Possible SSRF and Credential Leakage via Absolute URL"
                },
                "info": [
                    "https://github.com/advisories/GHSA-jr5f-v2jv-69x6",
                    "https://github.com/axios/axios",
                    "https://github.com/axios/axios/commit/fb8eec214ce7744b5ca787f2c3b8339b2f54b00f",
                    "https://github.com/axios/axios/issues/6463",
                    "https://github.com/axios/axios/releases/tag/v1.8.2",
                    "https://github.com/axios/axios/security/advisories/GHSA-jr5f-v2jv-69x6",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-27152"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.0.0",
                "below": "1.6.0",
                "cwe": [
                    "CWE-352"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-45857"
                    ],
                    "githubID": "GHSA-wf5p-g6vw-rhxx",
                    "summary": "Axios Cross-Site Request Forgery Vulnerability"
                },
                "info": [
                    "https://github.com/advisories/GHSA-wf5p-g6vw-rhxx",
                    "https://github.com/axios/axios/commit/96ee232bd3ee4de2e657333d4d2191cd389e14d0",
                    "https://github.com/axios/axios/issues/6006",
                    "https://github.com/axios/axios/issues/6022",
                    "https://github.com/axios/axios/pull/6028",
                    "https://github.com/axios/axios/releases/tag/v1.6.0",
                    "https://nvd.nist.gov/vuln/detail/CVE-2023-45857",
                    "https://security.snyk.io/vuln/SNYK-JS-AXIOS-6032459"
                ],
                "severity": "medium"
            },
            {
                "below": "1.6.8",
                "cwe": [
                    "CWE-200"
                ],
                "identifiers": {
                    "PR": "6300",
                    "summary": "Versions before 1.6.8 depends on follow-redirects before 1.15.6 which could leak the proxy authentication credentials"
                },
                "info": [
                    "https://github.com/axios/axios/pull/6300"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.3.2",
                "below": "1.7.4",
                "cwe": [
                    "CWE-918"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-39338"
                    ],
                    "githubID": "GHSA-8hc4-vh64-cxmj",
                    "summary": "Server-Side Request Forgery in axios"
                },
                "info": [
                    "https://github.com/advisories/GHSA-8hc4-vh64-cxmj",
                    "https://github.com/axios/axios",
                    "https://github.com/axios/axios/commit/6b6b605eaf73852fb2dae033f1e786155959de3a",
                    "https://github.com/axios/axios/issues/6463",
                    "https://github.com/axios/axios/pull/6539",
                    "https://github.com/axios/axios/pull/6543",
                    "https://github.com/axios/axios/releases",
                    "https://github.com/axios/axios/releases/tag/v1.7.4",
                    "https://jeffhacks.com/advisories/2024/06/24/CVE-2024-39338.html",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-39338"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.0.0",
                "below": "1.8.2",
                "cwe": [
                    "CWE-918"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-27152"
                    ],
                    "githubID": "GHSA-jr5f-v2jv-69x6",
                    "summary": "axios Requests Vulnerable To Possible SSRF and Credential Leakage via Absolute URL"
                },
                "info": [
                    "https://github.com/advisories/GHSA-jr5f-v2jv-69x6",
                    "https://github.com/axios/axios",
                    "https://github.com/axios/axios/commit/fb8eec214ce7744b5ca787f2c3b8339b2f54b00f",
                    "https://github.com/axios/axios/issues/6463",
                    "https://github.com/axios/axios/releases/tag/v1.8.2",
                    "https://github.com/axios/axios/security/advisories/GHSA-jr5f-v2jv-69x6",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-27152"
                ],
                "severity": "high"
            }
        ]
    },
    "backbone.js": {
        "basePurl": "pkg:npm/backbone",
        "bowername": [
            "backbone",
            "backbonejs"
        ],
        "extractors": {
            "filecontent": [
                "//[ ]+Backbone.js ([0-9][0-9.a-z_-]+)",
                "Backbone\\.VERSION *= *[\"']([0-9][0-9.a-z_-]+)[\"']",
                "a=t.Backbone=\\{\\}\\}a.VERSION=\"([0-9][0-9.a-z_-]+)\""
            ],
            "filename": [
                "backbone(?:js)?-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "Backbone.VERSION"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/backbone(\\.min)?\\.js"
            ]
        },
        "npmname": "backbone",
        "vulnerabilities": [
            {
                "below": "0.5.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2016-10537"
                    ],
                    "githubID": "GHSA-j6p2-cx3w-6jcp",
                    "release": "0.5.0",
                    "retid": "46",
                    "summary": "cross-site scripting vulnerability"
                },
                "info": [
                    "http://backbonejs.org/#changelog"
                ],
                "severity": "medium"
            }
        ]
    },
    "blueimp-file-upload": {
        "extractors": {
            "filecontent": [
                "/\\*[\\s*]+jQuery File Upload User Interface Plugin ([0-9][0-9.a-z_-]+)[\\s*]+https://github.com/blueimp"
            ],
            "uri": [
                "/blueimp-file-upload/([0-9][0-9.a-z_-]+)/jquery.fileupload(-ui)?(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "9.22.1",
                "cwe": [
                    "CWE-434"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-9206"
                    ],
                    "githubID": "GHSA-4cj8-g9cp-v5wr",
                    "summary": "Unrestricted Upload of File with Dangerous Type in blueimp-file-upload"
                },
                "info": [
                    "http://www.securityfocus.com/bid/105679",
                    "http://www.securityfocus.com/bid/106629",
                    "http://www.vapidlabs.com/advisory.php?v=204",
                    "https://github.com/advisories/GHSA-4cj8-g9cp-v5wr",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-9206",
                    "https://wpvulndb.com/vulnerabilities/9136",
                    "https://www.exploit-db.com/exploits/45790/",
                    "https://www.exploit-db.com/exploits/46182/",
                    "https://www.oracle.com/technetwork/security-advisory/cpujan2019-5072801.html"
                ],
                "severity": "high"
            }
        ]
    },
    "bootstrap": {
        "extractors": {
            "filecontent": [
                "/\\*! Bootstrap v([0-9][0-9.a-z_-]+)",
                "/\\*!? Bootstrap v([0-9][0-9.a-z_-]+)",
                "\\* Bootstrap v([0-9][0-9.a-z_-]+)",
                "this\\.close\\)\\};.\\.VERSION=\"([0-9][0-9.a-z_-]+)\"(?:,.\\.TRANSITION_DURATION=150)?,.\\.prototype\\.close"
            ],
            "filename": [
                "bootstrap-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/bootstrap(\\.min)?\\.js",
                "/([0-9][0-9.a-z_-]+)/js/bootstrap(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "2.1.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "issue": "3421",
                    "summary": "cross-site scripting vulnerability"
                },
                "info": [
                    "https://github.com/twbs/bootstrap/pull/3421"
                ],
                "severity": "medium"
            },
            {
                "below": "3.4.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-20676"
                    ],
                    "githubID": "GHSA-3mgp-fx93-9xv5",
                    "issue": "27044",
                    "summary": "In Bootstrap before 3.4.0, XSS is possible in the tooltip data-viewport attribute."
                },
                "info": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-20676"
                ],
                "severity": "medium"
            },
            {
                "below": "3.4.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-14042"
                    ],
                    "githubID": "GHSA-7mvr-5x2g-wfc8",
                    "issue": "20184",
                    "summary": "XSS in data-container property of tooltip"
                },
                "info": [
                    "https://github.com/twbs/bootstrap/issues/20184"
                ],
                "severity": "medium"
            },
            {
                "below": "3.4.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-20677"
                    ],
                    "githubID": "GHSA-ph58-4vrj-w6hr",
                    "summary": "In Bootstrap before 3.4.0, XSS is possible in the affix configuration target property."
                },
                "info": [
                    "https://github.com/advisories/GHSA-ph58-4vrj-w6hr"
                ],
                "severity": "medium"
            },
            {
                "below": "3.4.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-14041"
                    ],
                    "githubID": "GHSA-pj7m-g53m-7638",
                    "issue": "20184",
                    "summary": "XSS in data-target property of scrollspy"
                },
                "info": [
                    "https://github.com/advisories/GHSA-pj7m-g53m-7638",
                    "https://github.com/twbs/bootstrap/issues/20184"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.0.0",
                "below": "3.4.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2016-10735"
                    ],
                    "githubID": "GHSA-4p24-vmcr-4gqj",
                    "summary": "XSS is possible in the data-target attribute."
                },
                "info": [
                    "https://github.com/advisories/GHSA-4p24-vmcr-4gqj"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.4.0",
                "below": "3.4.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-6485"
                    ],
                    "githubID": "GHSA-vxmc-5x29-h64v",
                    "summary": "Bootstrap Cross-Site Scripting (XSS) vulnerability for data-* attributes"
                },
                "info": [
                    "https://github.com/advisories/GHSA-vxmc-5x29-h64v",
                    "https://github.com/twbs/bootstrap",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-6485",
                    "https://www.herodevs.com/vulnerability-directory/cve-2024-6485"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.0.0",
                "below": "3.4.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-8331"
                    ],
                    "githubID": "GHSA-9v3m-8fp8-mj99",
                    "issue": "28236",
                    "summary": "XSS in data-template, data-content and data-title properties of tooltip/popover"
                },
                "info": [
                    "https://github.com/advisories/GHSA-9v3m-8fp8-mj99",
                    "https://github.com/twbs/bootstrap/issues/28236"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "2.0.0",
                "below": "3.4.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-6484"
                    ],
                    "githubID": "GHSA-9mvj-f7w8-pvh2",
                    "summary": "Bootstrap Cross-Site Scripting (XSS) vulnerability"
                },
                "info": [
                    "https://github.com/advisories/GHSA-9mvj-f7w8-pvh2",
                    "https://github.com/rubysec/ruby-advisory-db/blob/master/gems/bootstrap-sass/CVE-2024-6484.yml",
                    "https://github.com/rubysec/ruby-advisory-db/blob/master/gems/bootstrap/CVE-2024-6484.yml",
                    "https://github.com/twbs/bootstrap",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-6484",
                    "https://www.herodevs.com/vulnerability-directory/cve-2024-6484"
                ],
                "severity": "medium"
            },
            {
                "below": "3.999.999",
                "cwe": [
                    "CWE-1104"
                ],
                "identifiers": {
                    "retid": "72",
                    "summary": "Bootstrap before 4.0.0 is end-of-life and no longer maintained."
                },
                "info": [
                    "https://github.com/twbs/bootstrap/issues/20631"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "4.0.0-beta",
                "below": "4.0.0-beta.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2016-10735"
                    ],
                    "githubID": "GHSA-4p24-vmcr-4gqj",
                    "summary": "XSS is possible in the data-target attribute."
                },
                "info": [
                    "https://github.com/advisories/GHSA-4p24-vmcr-4gqj"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.1.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-14040"
                    ],
                    "githubID": "GHSA-3wqf-4x89-9g79",
                    "issue": "20184",
                    "summary": "XSS in collapse data-parent attribute"
                },
                "info": [
                    "https://github.com/twbs/bootstrap/issues/20184"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.1.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-14042"
                    ],
                    "githubID": "GHSA-7mvr-5x2g-wfc8",
                    "issue": "20184",
                    "summary": "XSS in data-container property of tooltip"
                },
                "info": [
                    "https://github.com/twbs/bootstrap/issues/20184"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.1.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-14041"
                    ],
                    "githubID": "GHSA-pj7m-g53m-7638",
                    "issue": "20184",
                    "summary": "XSS in data-target property of scrollspy"
                },
                "info": [
                    "https://github.com/advisories/GHSA-pj7m-g53m-7638",
                    "https://github.com/twbs/bootstrap/issues/20184"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.3.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-8331"
                    ],
                    "githubID": "GHSA-9v3m-8fp8-mj99",
                    "issue": "28236",
                    "summary": "XSS in data-template, data-content and data-title properties of tooltip/popover"
                },
                "info": [
                    "https://github.com/advisories/GHSA-9v3m-8fp8-mj99",
                    "https://github.com/twbs/bootstrap/issues/28236"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "5.0.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-6531"
                    ],
                    "githubID": "GHSA-vc8w-jr9v-vj7f",
                    "summary": "Bootstrap Cross-Site Scripting (XSS) vulnerability"
                },
                "info": [
                    "https://github.com/advisories/GHSA-vc8w-jr9v-vj7f",
                    "https://github.com/rubysec/ruby-advisory-db/blob/master/gems/bootstrap/CVE-2024-6531.yml",
                    "https://github.com/twbs/bootstrap",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-6531",
                    "https://www.herodevs.com/vulnerability-directory/cve-2024-6531"
                ],
                "severity": "medium"
            }
        ]
    },
    "bootstrap-select": {
        "extractors": {
            "filecontent": [
                ".\\.data\\(\"selectpicker\",.=new .\\(this,.\\)\\)\\}\"string\"==typeof .&&\\(.=.\\[.\\]instanceof Function\\?.\\[.\\]\\.apply\\(.,.\\):.\\.options\\[.\\]\\)\\}\\}\\);return void 0!==.\\?.:.\\}.\\.VERSION=\"([0-9][0-9.a-z_-]+)\",",
                "/\\*![\\s]+\\*[\\s]+Bootstrap-select[\\s]+v([0-9][0-9.a-z_-]+)"
            ],
            "uri": [
                "/bootstrap-select/([0-9][0-9.a-z_-]+)/"
            ]
        },
        "vulnerabilities": [
            {
                "below": "1.13.6",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-20921"
                    ],
                    "githubID": "GHSA-7c82-mp33-r854",
                    "summary": "Cross-site Scripting (XSS) via title and data-content"
                },
                "info": [
                    "https://github.com/snapappointments/bootstrap-select/issues/2199#issuecomment-701806876"
                ],
                "severity": "medium"
            },
            {
                "below": "1.13.6",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-20921"
                    ],
                    "githubID": "GHSA-9r7h-6639-v5mw",
                    "summary": "Cross-Site Scripting in bootstrap-select"
                },
                "info": [
                    "https://github.com/snapappointments/bootstrap-select/issues/2199"
                ],
                "severity": "high"
            }
        ]
    },
    "c3": {
        "extractors": {
            "filecontent": [
                "[\\s]+var c3 ?= ?\\{ ?version: ?['\"]([0-9][0-9.a-z_-]+)['\"] ?\\};[\\s]+var c3_chart_fn,"
            ],
            "uri": [
                "/([0-9][0-9.a-z_-]+)/c3(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "0.4.11",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2016-1000240"
                    ],
                    "githubID": "GHSA-gvg7-pp82-cff3",
                    "summary": "Cross-Site Scripting in c3"
                },
                "info": [
                    "https://github.com/advisories/GHSA-gvg7-pp82-cff3",
                    "https://github.com/c3js/c3",
                    "https://github.com/c3js/c3/commit/de3864650300488a63d0541620e9828b00e94b42",
                    "https://github.com/c3js/c3/issues/1536",
                    "https://github.com/c3js/c3/pull/1675",
                    "https://nvd.nist.gov/vuln/detail/CVE-2016-1000240",
                    "https://www.npmjs.com/advisories/138"
                ],
                "severity": "medium"
            }
        ]
    },
    "chart.js": {
        "extractors": {
            "filecontent": [
                "/\\*![\\s]+\\* Chart.js v([0-9][0-9.a-z_-]+)",
                "/\\*![\\s]+\\* Chart.js[\\s]+\\* http://chartjs.org/[\\s]+\\* Version: ([0-9][0-9.a-z_-]+)",
                "var version=\"([0-9][0-9.a-z_-]+)\";const KNOWN_POSITIONS=\\[\"top\",\"bottom\",\"left\",\"right\",\"chartArea\"\\]"
            ],
            "uri": [
                "/Chart.js/([0-9][0-9.a-z_-]+)/Chart.bundle(\\.min)?\\.js",
                "/Chart.js/([0-9][0-9.a-z_-]+)/chart(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "2.9.4",
                "cwe": [
                    "CWE-1321",
                    "CWE-915"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-7746"
                    ],
                    "githubID": "GHSA-h68q-55jf-x68w",
                    "summary": "Prototype pollution in chart.js"
                },
                "info": [
                    "https://github.com/advisories/GHSA-h68q-55jf-x68w"
                ],
                "severity": "high"
            }
        ]
    },
    "ckeditor": {
        "extractors": {
            "filecontent": [
                "ckeditor..js.{4,30}=\\{timestamp:\"[^\"]+\",version:\"([0-9][0-9.a-z_-]+)",
                "window\\.CKEDITOR=function\\(\\)\\{var [a-z]=\\{timestamp:\"[^\"]+\",version:\"([0-9][0-9.a-z_-]+)"
            ],
            "filename": [
                "ckeditor-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "CKEDITOR.version"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/ckeditor(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "4.4.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "13",
                    "summary": "XSS"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor-dev/blob/master/CHANGES.md#ckeditor-443"
                ],
                "severity": "medium"
            },
            {
                "below": "4.4.6",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "14",
                    "summary": "XSS"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor-dev/blob/master/CHANGES.md#ckeditor-446"
                ],
                "severity": "medium"
            },
            {
                "below": "4.4.8",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "15",
                    "summary": "XSS"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor-dev/blob/master/CHANGES.md#ckeditor-448"
                ],
                "severity": "medium"
            },
            {
                "below": "4.5.11",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "16",
                    "summary": "XSS"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor-dev/blob/master/CHANGES.md#ckeditor-4511"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.5.11",
                "below": "4.9.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "17",
                    "summary": "XSS if the enhanced image plugin is installed"
                },
                "info": [
                    "https://ckeditor.com/blog/CKEditor-4.9.2-with-a-security-patch-released/",
                    "https://ckeditor.com/cke4/release-notes"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.11.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-17960"
                    ],
                    "githubID": "GHSA-g68x-vvqq-pvw3",
                    "retid": "18",
                    "summary": "XSS vulnerability in the HTML parser"
                },
                "info": [
                    "https://ckeditor.com/blog/CKEditor-4.11-with-emoji-dropdown-and-auto-link-on-typing-released/",
                    "https://snyk.io/vuln/SNYK-JS-CKEDITOR-72618"
                ],
                "severity": "medium"
            },
            {
                "below": "4.14.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "20",
                    "summary": "XSS"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor4/blob/major/CHANGES.md#ckeditor-414"
                ],
                "severity": "low"
            },
            {
                "below": "4.15.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "19",
                    "summary": "XSS-type attack inside CKEditor 4 by persuading a victim to paste a specially crafted HTML code into the Color Button dialog"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor4/blob/major/CHANGES.md#ckeditor-4151"
                ],
                "severity": "medium"
            },
            {
                "below": "4.16.0",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "retid": "21",
                    "summary": "ReDoS vulnerability in Autolink plugin and Advanced Tab for Dialogs plugin"
                },
                "info": [
                    "https://ckeditor.com/cke4/release/CKEditor-4.16.0"
                ],
                "severity": "low"
            },
            {
                "below": "4.16.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-32808"
                    ],
                    "summary": "XSS vulnerability in the Widget plugin"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor4/security/advisories/GHSA-6226-h7ff-ch6c"
                ],
                "severity": "low"
            },
            {
                "below": "4.16.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-32809"
                    ],
                    "summary": "XSS vulnerability in the Clipboard plugin"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor4/security/advisories/GHSA-7889-rm5j-hpgg"
                ],
                "severity": "low"
            },
            {
                "below": "4.16.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-37695"
                    ],
                    "summary": "XSS vulnerability in the Fake Objects plugin"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor4/security/advisories/GHSA-m94c-37g6-cjhc"
                ],
                "severity": "medium"
            },
            {
                "below": "4.17.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-41164",
                        "CVE-2021-41165"
                    ],
                    "summary": "XSS vulnerabilities in the core module"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor4/security/advisories/GHSA-7h26-63m7-qhf2",
                    "https://github.com/ckeditor/ckeditor4/security/advisories/GHSA-pvmx-g8h5-cprj"
                ],
                "severity": "medium"
            },
            {
                "below": "4.18.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-24728"
                    ],
                    "summary": "Inject malformed URL to bypass content sanitization for XSS"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor4/security/advisories/GHSA-f6rf-9m92-x2hh"
                ],
                "severity": "low"
            },
            {
                "below": "4.21.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-28439"
                    ],
                    "summary": "cross-site scripting vulnerability has been discovered affecting Iframe Dialog and Media Embed packages. The vulnerability may trigger a JavaScript code"
                },
                "info": [
                    "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-28439",
                    "https://github.com/ckeditor/ckeditor4/security/advisories/GHSA-vh5c-xwqv-cv9g",
                    "https://nvd.nist.gov/vuln/detail/CVE-2023-28439"
                ],
                "severity": "medium"
            }
        ]
    },
    "ckeditor5": {
        "extractors": {
            "filecontent": [
                "CKEDITOR_VERSION=\"([0-9][0-9.a-z_-]+)\"",
                "const .=\"([0-9][0-9.a-z_-]+)\";.{0,140}?\\.CKEDITOR_VERSION=.;"
            ],
            "filename": [
                "ckeditor5-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "CKEDITOR_VERSION"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/ckeditor5(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "10.0.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-11093"
                    ],
                    "summary": "XSS in the link package"
                },
                "info": [
                    "https://ckeditor.com/blog/CKEditor-5-v10.0.1-released/"
                ],
                "severity": "low"
            },
            {
                "below": "25.0.0",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-21254"
                    ],
                    "summary": "ReDos in several packages"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor5/security/advisories/GHSA-hgmg-hhc8-g5wr"
                ],
                "severity": "low"
            },
            {
                "below": "27.0.0",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-21391"
                    ],
                    "summary": "ReDos in several packages"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor5/security/advisories/GHSA-3rh3-wfr4-76mj"
                ],
                "severity": "low"
            },
            {
                "below": "35.0.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-31175"
                    ],
                    "summary": "security fix for the Markdown GFM, HTML support and HTML embed packages"
                },
                "info": [
                    "https://github.com/ckeditor/ckeditor5/compare/v34.2.0...v35.0.0",
                    "https://github.com/ckeditor/ckeditor5/security/advisories/GHSA-42wq-rch8-6f6j"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "40.0.0",
                "below": "43.1.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-45613"
                    ],
                    "githubID": "GHSA-rgg8-g5x8-wr9v",
                    "summary": "Cross-site scripting (XSS) in the clipboard package"
                },
                "info": [
                    "https://github.com/advisories/GHSA-rgg8-g5x8-wr9v",
                    "https://github.com/ckeditor/ckeditor5",
                    "https://github.com/ckeditor/ckeditor5/releases/tag/v43.1.1",
                    "https://github.com/ckeditor/ckeditor5/security/advisories/GHSA-rgg8-g5x8-wr9v",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-45613"
                ],
                "severity": "medium"
            }
        ]
    },
    "dojo": {
        "extractors": {
            "filecontentreplace": [
                "/\"dojox\"[\\s\\S]{1,350}\\.version=\\{major:([0-9]+),minor:([0-9]+),patch:([0-9]+)/$1.$2.$3/",
                "/dojo.version=\\{major:([0-9]+),minor:([0-9]+),patch:([0-9]+)/$1.$2.$3/"
            ],
            "filename": [
                "dojo-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "dojo.version.toString()"
            ],
            "hashes": {
                "12208a1e649402e362f528f6aae2c614fc697f8f": "1.2.0",
                "2ab48d45abe2f54cdda6ca32193b5ceb2b1bc25d": "1.2.3",
                "72a6a9fbef9fa5a73cd47e49942199147f905206": "1.1.1",
                "73cdd262799aab850abbe694cd3bfb709ea23627": "1.4.1",
                "8fc10142a06966a8709cd9b8732f7b6db88d0c34": "1.3.1",
                "a09b5851a0a3e9d81353745a4663741238ee1b84": "1.3.0",
                "ad44e1770895b7fa84aff5a56a0f99b855a83769": "1.3.2",
                "c8c84eddc732c3cbf370764836a7712f3f873326": "1.4.0",
                "d569ce9efb7edaedaec8ca9491aab0c656f7c8f0": "1.0.0"
            },
            "uri": [
                "/(?:dojo-)?([0-9][0-9.a-z_-]+)(?:/dojo)?/dojo(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "atOrAbove": "0.4",
                "below": "0.4.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2273"
                    ],
                    "PR": "307",
                    "githubID": "GHSA-536q-8gxx-m782",
                    "summary": "Versions of dojo prior to 1.4.2 are vulnerable to DOM-based Cross-Site Scripting (XSS). The package does not sanitize URL parameters in the _testCommon.js and runner.html test files, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "http://dojotoolkit.org/blog/dojo-security-advisory",
                    "http://www.cvedetails.com/cve/CVE-2010-2272/",
                    "http://www.cvedetails.com/cve/CVE-2010-2273/",
                    "http://www.cvedetails.com/cve/CVE-2010-2274/",
                    "http://www.cvedetails.com/cve/CVE-2010-2276/",
                    "https://dojotoolkit.org/blog/dojo-1-14-released",
                    "https://github.com/advisories/GHSA-536q-8gxx-m782",
                    "https://github.com/dojo/dojo/pull/307"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.0",
                "below": "1.0.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2273"
                    ],
                    "PR": "307",
                    "githubID": "GHSA-536q-8gxx-m782",
                    "summary": "Versions of dojo prior to 1.4.2 are vulnerable to DOM-based Cross-Site Scripting (XSS). The package does not sanitize URL parameters in the _testCommon.js and runner.html test files, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "http://dojotoolkit.org/blog/dojo-security-advisory",
                    "http://www.cvedetails.com/cve/CVE-2010-2272/",
                    "http://www.cvedetails.com/cve/CVE-2010-2273/",
                    "http://www.cvedetails.com/cve/CVE-2010-2274/",
                    "http://www.cvedetails.com/cve/CVE-2010-2276/",
                    "https://dojotoolkit.org/blog/dojo-1-14-released",
                    "https://github.com/advisories/GHSA-536q-8gxx-m782",
                    "https://github.com/dojo/dojo/pull/307"
                ],
                "severity": "medium"
            },
            {
                "below": "1.1.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2008-6681"
                    ],
                    "githubID": "GHSA-39cx-xcwj-3rc4",
                    "summary": "Affected versions of dojo are susceptible to a cross-site scripting vulnerability in the dijit.Editor and textarea components, which execute their contents as Javascript, even when sanitized."
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2008-6681/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.1",
                "below": "1.1.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2273"
                    ],
                    "PR": "307",
                    "githubID": "GHSA-536q-8gxx-m782",
                    "summary": "Versions of dojo prior to 1.4.2 are vulnerable to DOM-based Cross-Site Scripting (XSS). The package does not sanitize URL parameters in the _testCommon.js and runner.html test files, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "http://dojotoolkit.org/blog/dojo-security-advisory",
                    "http://www.cvedetails.com/cve/CVE-2010-2272/",
                    "http://www.cvedetails.com/cve/CVE-2010-2273/",
                    "http://www.cvedetails.com/cve/CVE-2010-2274/",
                    "http://www.cvedetails.com/cve/CVE-2010-2276/",
                    "https://dojotoolkit.org/blog/dojo-1-14-released",
                    "https://github.com/advisories/GHSA-536q-8gxx-m782",
                    "https://github.com/dojo/dojo/pull/307"
                ],
                "severity": "medium"
            },
            {
                "below": "1.2.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-5654"
                    ],
                    "githubID": "GHSA-p82g-2xpp-m5r3",
                    "summary": "Versions of dojo prior to 1.2.0 are vulnerable to Cross-Site Scripting (XSS). The package fails to sanitize HTML code in user-controlled input, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2015-5654"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.2",
                "below": "1.2.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2273"
                    ],
                    "PR": "307",
                    "githubID": "GHSA-536q-8gxx-m782",
                    "summary": "Versions of dojo prior to 1.4.2 are vulnerable to DOM-based Cross-Site Scripting (XSS). The package does not sanitize URL parameters in the _testCommon.js and runner.html test files, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "http://dojotoolkit.org/blog/dojo-security-advisory",
                    "http://www.cvedetails.com/cve/CVE-2010-2272/",
                    "http://www.cvedetails.com/cve/CVE-2010-2273/",
                    "http://www.cvedetails.com/cve/CVE-2010-2274/",
                    "http://www.cvedetails.com/cve/CVE-2010-2276/",
                    "https://dojotoolkit.org/blog/dojo-1-14-released",
                    "https://github.com/advisories/GHSA-536q-8gxx-m782",
                    "https://github.com/dojo/dojo/pull/307"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.3",
                "below": "1.3.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2273"
                    ],
                    "PR": "307",
                    "githubID": "GHSA-536q-8gxx-m782",
                    "summary": "Versions of dojo prior to 1.4.2 are vulnerable to DOM-based Cross-Site Scripting (XSS). The package does not sanitize URL parameters in the _testCommon.js and runner.html test files, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "http://dojotoolkit.org/blog/dojo-security-advisory",
                    "http://www.cvedetails.com/cve/CVE-2010-2272/",
                    "http://www.cvedetails.com/cve/CVE-2010-2273/",
                    "http://www.cvedetails.com/cve/CVE-2010-2274/",
                    "http://www.cvedetails.com/cve/CVE-2010-2276/",
                    "https://dojotoolkit.org/blog/dojo-1-14-released",
                    "https://github.com/advisories/GHSA-536q-8gxx-m782",
                    "https://github.com/dojo/dojo/pull/307"
                ],
                "severity": "medium"
            },
            {
                "below": "1.4.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2275"
                    ],
                    "summary": "Cross-site scripting (XSS) vulnerability in dijit/tests/_testCommon.js in Dojo Toolkit SDK before 1.4.2 allows remote attackers to inject arbitrary web script or HTML via the theme parameter, as demonstrated by an attack against dijit/tests/form/test_Button.html"
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2010-2275/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.4",
                "below": "1.4.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2273"
                    ],
                    "PR": "307",
                    "githubID": "GHSA-536q-8gxx-m782",
                    "summary": "Versions of dojo prior to 1.4.2 are vulnerable to DOM-based Cross-Site Scripting (XSS). The package does not sanitize URL parameters in the _testCommon.js and runner.html test files, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "http://dojotoolkit.org/blog/dojo-security-advisory",
                    "http://www.cvedetails.com/cve/CVE-2010-2272/",
                    "http://www.cvedetails.com/cve/CVE-2010-2273/",
                    "http://www.cvedetails.com/cve/CVE-2010-2274/",
                    "http://www.cvedetails.com/cve/CVE-2010-2276/",
                    "https://dojotoolkit.org/blog/dojo-1-14-released",
                    "https://github.com/advisories/GHSA-536q-8gxx-m782",
                    "https://github.com/dojo/dojo/pull/307"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.10.0",
                "below": "1.10.10",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2273"
                    ],
                    "PR": "307",
                    "githubID": "GHSA-536q-8gxx-m782",
                    "summary": "Versions of dojo prior to 1.4.2 are vulnerable to DOM-based Cross-Site Scripting (XSS). The package does not sanitize URL parameters in the _testCommon.js and runner.html test files, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "http://dojotoolkit.org/blog/dojo-security-advisory",
                    "http://www.cvedetails.com/cve/CVE-2010-2272/",
                    "http://www.cvedetails.com/cve/CVE-2010-2273/",
                    "http://www.cvedetails.com/cve/CVE-2010-2274/",
                    "http://www.cvedetails.com/cve/CVE-2010-2276/",
                    "https://dojotoolkit.org/blog/dojo-1-14-released",
                    "https://github.com/advisories/GHSA-536q-8gxx-m782",
                    "https://github.com/dojo/dojo/pull/307"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.11.0",
                "below": "1.11.6",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2273"
                    ],
                    "PR": "307",
                    "githubID": "GHSA-536q-8gxx-m782",
                    "summary": "Versions of dojo prior to 1.4.2 are vulnerable to DOM-based Cross-Site Scripting (XSS). The package does not sanitize URL parameters in the _testCommon.js and runner.html test files, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "http://dojotoolkit.org/blog/dojo-security-advisory",
                    "http://www.cvedetails.com/cve/CVE-2010-2272/",
                    "http://www.cvedetails.com/cve/CVE-2010-2273/",
                    "http://www.cvedetails.com/cve/CVE-2010-2274/",
                    "http://www.cvedetails.com/cve/CVE-2010-2276/",
                    "https://dojotoolkit.org/blog/dojo-1-14-released",
                    "https://github.com/advisories/GHSA-536q-8gxx-m782",
                    "https://github.com/dojo/dojo/pull/307"
                ],
                "severity": "medium"
            },
            {
                "below": "1.11.10",
                "cwe": [
                    "CWE-1321",
                    "CWE-74",
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-5258"
                    ],
                    "githubID": "GHSA-jxfh-8wgv-vfr2",
                    "summary": "Prototype pollution in dojo"
                },
                "info": [
                    "https://github.com/advisories/GHSA-jxfh-8wgv-vfr2",
                    "https://github.com/dojo/dojo/security/advisories/GHSA-jxfh-8wgv-vfr2"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.12.0",
                "below": "1.12.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2273"
                    ],
                    "PR": "307",
                    "githubID": "GHSA-536q-8gxx-m782",
                    "summary": "Versions of dojo prior to 1.4.2 are vulnerable to DOM-based Cross-Site Scripting (XSS). The package does not sanitize URL parameters in the _testCommon.js and runner.html test files, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "http://dojotoolkit.org/blog/dojo-security-advisory",
                    "http://www.cvedetails.com/cve/CVE-2010-2272/",
                    "http://www.cvedetails.com/cve/CVE-2010-2273/",
                    "http://www.cvedetails.com/cve/CVE-2010-2274/",
                    "http://www.cvedetails.com/cve/CVE-2010-2276/",
                    "https://dojotoolkit.org/blog/dojo-1-14-released",
                    "https://github.com/advisories/GHSA-536q-8gxx-m782",
                    "https://github.com/dojo/dojo/pull/307"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.12.0",
                "below": "1.12.8",
                "cwe": [
                    "CWE-1321",
                    "CWE-74",
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-5258"
                    ],
                    "githubID": "GHSA-jxfh-8wgv-vfr2",
                    "summary": "Prototype pollution in dojo"
                },
                "info": [
                    "https://github.com/advisories/GHSA-jxfh-8wgv-vfr2",
                    "https://github.com/dojo/dojo/security/advisories/GHSA-jxfh-8wgv-vfr2"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.13.0",
                "below": "1.13.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-2273"
                    ],
                    "PR": "307",
                    "githubID": "GHSA-536q-8gxx-m782",
                    "summary": "Versions of dojo prior to 1.4.2 are vulnerable to DOM-based Cross-Site Scripting (XSS). The package does not sanitize URL parameters in the _testCommon.js and runner.html test files, allowing attackers to execute arbitrary JavaScript in the victim's browser."
                },
                "info": [
                    "http://dojotoolkit.org/blog/dojo-security-advisory",
                    "http://www.cvedetails.com/cve/CVE-2010-2272/",
                    "http://www.cvedetails.com/cve/CVE-2010-2273/",
                    "http://www.cvedetails.com/cve/CVE-2010-2274/",
                    "http://www.cvedetails.com/cve/CVE-2010-2276/",
                    "https://dojotoolkit.org/blog/dojo-1-14-released",
                    "https://github.com/advisories/GHSA-536q-8gxx-m782",
                    "https://github.com/dojo/dojo/pull/307"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.13.0",
                "below": "1.13.7",
                "cwe": [
                    "CWE-1321",
                    "CWE-74",
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-5258"
                    ],
                    "githubID": "GHSA-jxfh-8wgv-vfr2",
                    "summary": "Prototype pollution in dojo"
                },
                "info": [
                    "https://github.com/advisories/GHSA-jxfh-8wgv-vfr2",
                    "https://github.com/dojo/dojo/security/advisories/GHSA-jxfh-8wgv-vfr2"
                ],
                "severity": "high"
            },
            {
                "below": "1.14",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-15494"
                    ],
                    "githubID": "GHSA-84cm-x2q5-8225",
                    "summary": "In Dojo Toolkit before 1.14.0, there is unescaped string injection in dojox/Grid/DataGrid."
                },
                "info": [
                    "https://dojotoolkit.org/blog/dojo-1-14-released"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.14.0",
                "below": "1.14.6",
                "cwe": [
                    "CWE-1321",
                    "CWE-74",
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-5258"
                    ],
                    "githubID": "GHSA-jxfh-8wgv-vfr2",
                    "summary": "Prototype pollution in dojo"
                },
                "info": [
                    "https://github.com/advisories/GHSA-jxfh-8wgv-vfr2",
                    "https://github.com/dojo/dojo/security/advisories/GHSA-jxfh-8wgv-vfr2"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.15.0",
                "below": "1.15.3",
                "cwe": [
                    "CWE-1321",
                    "CWE-74",
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-5258"
                    ],
                    "githubID": "GHSA-jxfh-8wgv-vfr2",
                    "summary": "Prototype pollution in dojo"
                },
                "info": [
                    "https://github.com/advisories/GHSA-jxfh-8wgv-vfr2",
                    "https://github.com/dojo/dojo/security/advisories/GHSA-jxfh-8wgv-vfr2"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.16.0",
                "below": "1.16.2",
                "cwe": [
                    "CWE-1321",
                    "CWE-74",
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-5258"
                    ],
                    "githubID": "GHSA-jxfh-8wgv-vfr2",
                    "summary": "Prototype pollution in dojo"
                },
                "info": [
                    "https://github.com/advisories/GHSA-jxfh-8wgv-vfr2",
                    "https://github.com/dojo/dojo/security/advisories/GHSA-jxfh-8wgv-vfr2"
                ],
                "severity": "high"
            },
            {
                "below": "1.17.0",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-23450"
                    ],
                    "githubID": "GHSA-m8gw-hjpr-rjv7",
                    "summary": "Prototype pollution"
                },
                "info": [
                    "https://github.com/dojo/dojo/pull/418"
                ],
                "severity": "high"
            }
        ]
    },
    "dont check": {
        "extractors": {
            "uri": [
                "^http[s]?://(ssl|www).google-analytics.com/ga.js",
                "^http[s]?://apis.google.com/js/plusone.js",
                "^http[s]?://cdn.cxense.com/cx.js"
            ]
        },
        "vulnerabilities": []
    },
    "easyXDM": {
        "extractors": {
            "filecontent": [
                " \\* easyXDM\n \\* http://easyxdm.net/(?:\r|\n|.)+version:\"([0-9][0-9.a-z_-]+)\"",
                "@class easyXDM(?:.|\r|\n)+@version ([0-9][0-9.a-z_-]+)(\r|\n)"
            ],
            "filename": [
                "easyXDM-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "hashes": {
                "cf266e3bc2da372c4f0d6b2bd87bcbaa24d5a643": "2.4.6"
            },
            "uri": [
                "/(?:easyXDM-)?([0-9][0-9.a-z_-]+)/easyXDM(\\.min)?\\.js"
            ]
        },
        "npmname": "easyxdm",
        "vulnerabilities": [
            {
                "below": "2.4.18",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-5212"
                    ]
                },
                "info": [
                    "http://blog.kotowicz.net/2013/09/exploiting-easyxdm-part-1-not-usual.html",
                    "http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2013-5212"
                ],
                "severity": "medium"
            },
            {
                "below": "2.4.19",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-1403"
                    ]
                },
                "info": [
                    "http://blog.kotowicz.net/2014/01/xssing-with-shakespeare-name-calling.html",
                    "http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2014-1403"
                ],
                "severity": "medium"
            },
            {
                "below": "2.4.20",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "39",
                    "summary": "This release fixes a potential XSS for IE running in compatibility mode."
                },
                "info": [
                    "https://github.com/oyvindkinsey/easyXDM/releases/tag/2.4.20"
                ],
                "severity": "medium"
            },
            {
                "below": "2.5.0",
                "cwe": [
                    "CWE-942"
                ],
                "identifiers": {
                    "retid": "40",
                    "summary": "This tightens down the default origin whitelist in the CORS example."
                },
                "info": [
                    "https://github.com/oyvindkinsey/easyXDM/releases/tag/2.5.0"
                ],
                "severity": "medium"
            }
        ]
    },
    "ember": {
        "extractors": {
            "filecontent": [
                "// Version: ([0-9][0-9.a-z_-]+)[\\s]+\\(function\\(\\) *\\{[\\s]*/\\*\\*[\\s]+@module ember[\\s]",
                "// Version: v([0-9][0-9.a-z_-]+)(.*\n){10,15}(Ember Debug|@module ember|@class ember)",
                "/\\*![\\s]+\\* @overview  Ember - JavaScript Application Framework[\\s\\S]{0,400}\\* @version   ([0-9][0-9.a-z_-]+)",
                "Ember.VERSION[ ]?=[ ]?(?:'|\")([0-9][0-9.a-z_-]+)(?:'|\")",
                "Project:   Ember -(?:.*\n){9,11}// Version: v([0-9][0-9.a-z_-]+)",
                "\\(\"ember/version\",\\[\"exports\"\\],function\\(e\\)\\{\"use strict\";.{1,70}\\.default=\"([0-9][0-9.a-z_-]+)\"",
                "e\\(\"ember/version\",\\[\"exports\"\\],function\\(e\\)\\{\"use strict\";?[\\s]*e(?:\\.|\\[\")default(?:\"\\])?=\"([0-9][0-9.a-z_-]+)\"",
                "meta\\.revision=\"Ember@([0-9][0-9.a-z_-]+)\""
            ],
            "filename": [
                "ember-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "Ember.VERSION"
            ],
            "hashes": {},
            "uri": [
                "/(?:v)?([0-9][0-9.a-z_-]+)/ember(\\.min)?\\.js",
                "/ember\\.?js/([0-9][0-9.a-z_-]+)/ember((\\.|-)[a-z\\-.]+)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "0.9.7",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "bug": "699",
                    "summary": "Bound attributes aren't escaped properly"
                },
                "info": [
                    "https://github.com/emberjs/ember.js/issues/699"
                ],
                "severity": "high"
            },
            {
                "below": "0.9.7.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "60",
                    "summary": "More rigorous XSS escaping from bindAttr"
                },
                "info": [
                    "https://github.com/emberjs/ember.js/blob/master/CHANGELOG.md"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.0.0-rc.1",
                "below": "1.0.0-rc.1.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4170"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/dokLVwwxAdM"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.0.0-rc.2",
                "below": "1.0.0-rc.2.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4170"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/dokLVwwxAdM"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.0.0-rc.3",
                "below": "1.0.0-rc.3.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4170"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/dokLVwwxAdM"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.0.0-rc.4",
                "below": "1.0.0-rc.4.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4170"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/dokLVwwxAdM"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.0.0-rc.5",
                "below": "1.0.0-rc.5.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4170"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/dokLVwwxAdM"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.0.0-rc.6",
                "below": "1.0.0-rc.6.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-4170"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/dokLVwwxAdM"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.0.0",
                "below": "1.0.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-0013",
                        "CVE-2014-0014"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/2kpXXCxISS4",
                    "https://groups.google.com/forum/#!topic/ember-security/PSE4RzTi6l4"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.1.0",
                "below": "1.1.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-0013",
                        "CVE-2014-0014"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/2kpXXCxISS4",
                    "https://groups.google.com/forum/#!topic/ember-security/PSE4RzTi6l4"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.2.0",
                "below": "1.2.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-0013",
                        "CVE-2014-0014"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/2kpXXCxISS4",
                    "https://groups.google.com/forum/#!topic/ember-security/PSE4RzTi6l4"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.2.0",
                "below": "1.2.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-0046"
                    ],
                    "summary": "ember-routing-auto-location can be forced to redirect to another domain"
                },
                "info": [
                    "https://github.com/emberjs/ember.js/blob/v1.5.0/CHANGELOG.md",
                    "https://groups.google.com/forum/#!topic/ember-security/1h6FRgr8lXQ"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.3.0",
                "below": "1.3.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-0013",
                        "CVE-2014-0014"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/2kpXXCxISS4",
                    "https://groups.google.com/forum/#!topic/ember-security/PSE4RzTi6l4"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.3.0",
                "below": "1.3.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-0046"
                    ],
                    "summary": "ember-routing-auto-location can be forced to redirect to another domain"
                },
                "info": [
                    "https://github.com/emberjs/ember.js/blob/v1.5.0/CHANGELOG.md",
                    "https://groups.google.com/forum/#!topic/ember-security/1h6FRgr8lXQ"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.4.0",
                "below": "1.4.0-beta.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-0013",
                        "CVE-2014-0014"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/2kpXXCxISS4",
                    "https://groups.google.com/forum/#!topic/ember-security/PSE4RzTi6l4"
                ],
                "severity": "low"
            },
            {
                "below": "1.5.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2014-0046"
                    ],
                    "summary": "ember-routing-auto-location can be forced to redirect to another domain"
                },
                "info": [
                    "https://github.com/emberjs/ember.js/blob/v1.5.0/CHANGELOG.md",
                    "https://groups.google.com/forum/#!topic/ember-security/1h6FRgr8lXQ"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.8.0",
                "below": "1.11.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-7565"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/OfyQkoSuppY"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.12.0",
                "below": "1.12.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-7565"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/OfyQkoSuppY"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.13.0",
                "below": "1.13.12",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-7565"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/OfyQkoSuppY"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "2.0.0",
                "below": "2.0.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-7565"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/OfyQkoSuppY"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "2.1.0",
                "below": "2.1.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-7565"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/OfyQkoSuppY"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "2.2.0",
                "below": "2.2.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-7565"
                    ]
                },
                "info": [
                    "https://groups.google.com/forum/#!topic/ember-security/OfyQkoSuppY"
                ],
                "severity": "medium"
            },
            {
                "below": "3.24.7",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "retid": "59",
                    "summary": "Prototype pollution"
                },
                "info": [
                    "https://blog.emberjs.com/ember-4-8-1-released/"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "3.25.0",
                "below": "3.28.10",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "retid": "58",
                    "summary": "Prototype pollution"
                },
                "info": [
                    "https://blog.emberjs.com/ember-4-8-1-released/"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.4.4",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "retid": "57",
                    "summary": "Prototype pollution"
                },
                "info": [
                    "https://blog.emberjs.com/ember-4-8-1-released/"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.5.0",
                "below": "4.8.1",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "retid": "56",
                    "summary": "Prototype pollution"
                },
                "info": [
                    "https://blog.emberjs.com/ember-4-8-1-released/"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.9.0-alpha.1",
                "below": "4.9.0-beta.3",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "retid": "55",
                    "summary": "Prototype pollution"
                },
                "info": [
                    "https://blog.emberjs.com/ember-4-8-1-released/"
                ],
                "severity": "high"
            }
        ]
    },
    "flowplayer": {
        "extractors": {
            "filename": [
                "flowplayer-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "uri": [
                "flowplayer-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "5.4.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "issue": "381",
                    "summary": "XSS vulnerability in Flash fallback"
                },
                "info": [
                    "https://github.com/flowplayer/flowplayer/issues/381"
                ],
                "severity": "medium"
            }
        ]
    },
    "froala": {
        "extractors": {
            "filecontent": [
                "/\\*![\\s]+\\* froala_editor v([0-9][0-9.a-z_-]+)",
                "VERSION:\"([0-9][0-9.a-z_-]+)\",INSTANCES:\\[\\],OPTS_MAPPING:\\{\\}"
            ],
            "func": [
                "FroalaEditor.VERSION"
            ],
            "uri": [
                "/froala-editor/([0-9][0-9.a-z_-]+)/",
                "/froala-editor@([0-9][0-9.a-z_-]+)/"
            ]
        },
        "npmname": "froala-editor",
        "vulnerabilities": [
            {
                "below": "3.2.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "issue": "3880",
                    "summary": "Security issue: XSS via pasted content"
                },
                "info": [
                    "https://froala.com/wysiwyg-editor/changelog/#3.2.2"
                ],
                "severity": "medium"
            },
            {
                "below": "3.2.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "issue": "3270",
                    "summary": "XSS Issue In Link Insertion"
                },
                "info": [
                    "https://github.com/froala/wysiwyg-editor/issues/3270"
                ],
                "severity": "medium"
            },
            {
                "below": "3.2.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-19935"
                    ],
                    "githubID": "GHSA-h236-g5gh-vq6c",
                    "summary": "DOM-based cross-site scripting in Froala Editor"
                },
                "info": [
                    "https://github.com/advisories/GHSA-h236-g5gh-vq6c"
                ],
                "severity": "medium"
            },
            {
                "below": "3.2.7",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-28114"
                    ],
                    "summary": "Froala WYSIWYG Editor 3.2.6-1 is affected by XSS due to a namespace confusion during parsing."
                },
                "info": [
                    "https://bishopfox.com/blog/froala-editor-v3-2-6-advisory"
                ],
                "severity": "high"
            },
            {
                "below": "3.2.7",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-30109"
                    ],
                    "githubID": "GHSA-cq6w-w5rj-p9x8",
                    "summary": "Froala WYSIWYG Editor 3.2.6 is affected by Cross Site Scripting (XSS). Under certain conditions, a base64 crafted string leads to persistent XSS."
                },
                "info": [
                    "https://github.com/froala/wysiwyg-editor/releases/tag/v4.0.11"
                ],
                "severity": "medium"
            },
            {
                "below": "4.0.11",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-22864"
                    ],
                    "githubID": "GHSA-97x5-cc53-cv4v",
                    "issue": "3880",
                    "summary": "XSS vulnerability in [insert video]"
                },
                "info": [
                    "https://github.com/froala/wysiwyg-editor/releases/tag/v4.0.11"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.0.1",
                "below": "4.1.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-41592"
                    ],
                    "githubID": "GHSA-hvpq-7vcc-5hj5",
                    "summary": "Froala Editor v4.0.1 to v4.1.1 was discovered to contain a cross-site scripting (XSS) vulnerability."
                },
                "info": [
                    "https://froala.com/wysiwyg-editor/changelog/#4.1.4",
                    "https://github.com/advisories/GHSA-hvpq-7vcc-5hj5"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "4.3.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-51434"
                    ],
                    "githubID": "GHSA-549p-5c7f-c5p4",
                    "summary": "Froala WYSIWYG editor allows cross-site scripting (XSS)"
                },
                "info": [
                    "https://georgyg.com/home/froala-wysiwyg-editor---xss-cve-2024-51434",
                    "https://github.com/advisories/GHSA-549p-5c7f-c5p4",
                    "https://github.com/froala/wysiwyg-editor",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-51434"
                ],
                "severity": "medium"
            }
        ]
    },
    "handlebars": {
        "bowername": [
            "handlebars",
            "handlebars.js"
        ],
        "extractors": {
            "filecontent": [
                ".\\.HandlebarsEnvironment=.;var .=.\\(.\\),.=.\\(.\\),.=\"([0-9][0-9.a-z_-]+)\";.\\.VERSION=",
                "/\\*+![\\s]+(?:@license)?[\\s]+handlebars v+([0-9][0-9.a-z_-]+)",
                "Handlebars.VERSION = \"([0-9][0-9.a-z_-]+)\";",
                "Handlebars=\\{VERSION:(?:'|\")([0-9][0-9.a-z_-]+)(?:'|\")",
                "exports.HandlebarsEnvironment=[\\s\\S]{70,120}exports.VERSION=(?:'|\")([0-9][0-9.a-z_-]+)(?:'|\")",
                "this.Handlebars=\\{\\};[\n\r \t]+\\(function\\([a-z]\\)\\{[a-z].VERSION=(?:'|\")([0-9][0-9.a-z_-]+)(?:'|\")",
                "window\\.Handlebars=.,.\\.VERSION=\"([0-9][0-9.a-z_-]+)\""
            ],
            "filename": [
                "handlebars(?:js)?-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "Handlebars.VERSION"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/handlebars(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "1.0.0.beta.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "issue": "68",
                    "summary": "poorly sanitized input passed to eval()"
                },
                "info": [
                    "https://github.com/wycats/handlebars.js/pull/68"
                ],
                "severity": "medium"
            },
            {
                "below": "3.0.7",
                "cwe": [
                    "CWE-471"
                ],
                "identifiers": {
                    "githubID": "GHSA-q42p-pg8m-cqh6",
                    "issue": "1495",
                    "summary": "A prototype pollution vulnerability in handlebars is exploitable if an attacker can control the template"
                },
                "info": [
                    "https://github.com/advisories/GHSA-q42p-pg8m-cqh6",
                    "https://github.com/wycats/handlebars.js/commit/cd38583216dce3252831916323202749431c773e",
                    "https://github.com/wycats/handlebars.js/issues/1495",
                    "https://snyk.io/vuln/SNYK-JS-HANDLEBARS-174183"
                ],
                "severity": "high"
            },
            {
                "below": "3.0.8",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "githubID": "GHSA-2cf5-4w76-r9qv",
                    "summary": "Versions of `handlebars` prior to 3.0.8 or 4.5.2 are vulnerable to Arbitrary Code Execution. The package's lookup helper fails to properly validate templates, allowing attackers to submit templates that execute arbitrary JavaScript in the system. It can be used to run arbitrary code in a server processing Handlebars templates or on a victim's browser (effectively serving as Cross-Site Scripting).\n\nThe following template can be used to demonstrate the vulnerability:  \n```{{#with \"constructor\"}}\n\t{{#with split as |a|}}\n\t\t{{pop (push \"alert('Vulnerable Handlebars JS');\")}}\n\t\t{{#with (concat (lookup join (slice 0 1)))}}\n\t\t\t{{#each (slice 2 3)}}\n\t\t\t\t{{#with (apply 0 a)}}\n\t\t\t\t\t{{.}}\n\t\t\t\t{{/with}}\n\t\t\t{{/each}}\n\t\t{{/with}}\n\t{{/with}}\n{{/with}}```\n\n\n## Recommendation\n\nUpgrade to version 3.0.8, 4.5.2 or later."
                },
                "info": [
                    "https://github.com/advisories/GHSA-2cf5-4w76-r9qv",
                    "https://www.npmjs.com/advisories/1316"
                ],
                "severity": "high"
            },
            {
                "below": "3.0.8",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-20920"
                    ],
                    "githubID": "GHSA-3cqr-58rm-57f8",
                    "summary": "Handlebars before 3.0.8 and 4.x before 4.5.3 is vulnerable to Arbitrary Code Execution. The lookup helper fails to properly validate templates, allowing attackers to submit templates that execute arbitrary JavaScript. This can be used to run arbitrary code on a server processing Handlebars templates or in a victim's browser (effectively serving as XSS)."
                },
                "info": [
                    "https://github.com/advisories/GHSA-3cqr-58rm-57f8",
                    "https://nvd.nist.gov/vuln/detail/CVE-2019-20920"
                ],
                "severity": "high"
            },
            {
                "below": "3.0.8",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "githubID": "GHSA-g9r4-xpmj-mj65",
                    "retid": "45",
                    "summary": "Prototype pollution"
                },
                "info": [
                    "https://github.com/advisories/GHSA-g9r4-xpmj-mj65",
                    "https://github.com/wycats/handlebars.js/blob/master/release-notes.md#v453---november-18th-2019"
                ],
                "severity": "high"
            },
            {
                "below": "3.0.8",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-q2c6-c6pm-g3gh",
                    "summary": "Versions of `handlebars` prior to 3.0.8 or 4.5.3 are vulnerable to Arbitrary Code Execution. The package's lookup helper fails to properly validate templates, allowing attackers to submit templates that execute arbitrary JavaScript in the system. It is due to an incomplete fix for a [previous issue](https://www.npmjs.com/advisories/1316). This vulnerability can be used to run arbitrary code in a server processing Handlebars templates or on a victim's browser (effectively serving as Cross-Site Scripting)"
                },
                "info": [
                    "https://github.com/advisories/GHSA-q2c6-c6pm-g3gh",
                    "https://github.com/wycats/handlebars.js/blob/master/release-notes.md#v453---november-18th-2019"
                ],
                "severity": "high"
            },
            {
                "below": "3.0.8",
                "cwe": [
                    "CWE-1321",
                    "CWE-74"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-19919"
                    ],
                    "githubID": "GHSA-w457-6q6x-cgp9",
                    "retid": "44",
                    "summary": "Disallow calling helperMissing and blockHelperMissing directly"
                },
                "info": [
                    "https://github.com/wycats/handlebars.js/blob/master/release-notes.md#v430---september-24th-2019"
                ],
                "severity": "high"
            },
            {
                "below": "4.0.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-8861"
                    ],
                    "githubID": "GHSA-9prh-257w-9277",
                    "issue": "1083",
                    "summary": "Quoteless attributes in templates can lead to XSS"
                },
                "info": [
                    "https://github.com/wycats/handlebars.js/pull/1083"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.0.13",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "retid": "43",
                    "summary": "A prototype pollution vulnerability in handlebars is exploitable if an attacker can control the template"
                },
                "info": [
                    "https://github.com/wycats/handlebars.js/commit/7372d4e9dffc9d70c09671aa28b9392a1577fd86",
                    "https://snyk.io/vuln/SNYK-JS-HANDLEBARS-173692"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.0.14",
                "cwe": [
                    "CWE-471"
                ],
                "identifiers": {
                    "githubID": "GHSA-q42p-pg8m-cqh6",
                    "issue": "1495",
                    "summary": "A prototype pollution vulnerability in handlebars is exploitable if an attacker can control the template"
                },
                "info": [
                    "https://github.com/advisories/GHSA-q42p-pg8m-cqh6",
                    "https://github.com/wycats/handlebars.js/commit/cd38583216dce3252831916323202749431c773e",
                    "https://github.com/wycats/handlebars.js/issues/1495",
                    "https://snyk.io/vuln/SNYK-JS-HANDLEBARS-174183"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.1.0",
                "below": "4.1.2",
                "cwe": [
                    "CWE-471"
                ],
                "identifiers": {
                    "githubID": "GHSA-q42p-pg8m-cqh6",
                    "issue": "1495",
                    "summary": "A prototype pollution vulnerability in handlebars is exploitable if an attacker can control the template"
                },
                "info": [
                    "https://github.com/advisories/GHSA-q42p-pg8m-cqh6",
                    "https://github.com/wycats/handlebars.js/commit/cd38583216dce3252831916323202749431c773e",
                    "https://github.com/wycats/handlebars.js/issues/1495",
                    "https://snyk.io/vuln/SNYK-JS-HANDLEBARS-174183"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.3.0",
                "cwe": [
                    "CWE-1321",
                    "CWE-74"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-19919"
                    ],
                    "githubID": "GHSA-w457-6q6x-cgp9",
                    "retid": "44",
                    "summary": "Disallow calling helperMissing and blockHelperMissing directly"
                },
                "info": [
                    "https://github.com/wycats/handlebars.js/blob/master/release-notes.md#v430---september-24th-2019"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.4.5",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-20922"
                    ],
                    "githubID": "GHSA-62gr-4qp9-h98f",
                    "summary": "Regular Expression Denial of Service in Handlebars"
                },
                "info": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2019-20922"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.4.5",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "githubID": "GHSA-f52g-6jhx-586p",
                    "retid": "75",
                    "summary": "Affected versions of `handlebars` are vulnerable to Denial of Service. The package's parser may be forced into an endless loop while processing specially-crafted templates. This may allow attackers to exhaust system resources leading to Denial of Service.\n\n\n## Recommendation\n\nUpgrade to version 4.4.5 or later."
                },
                "info": [
                    "https://github.com/handlebars-lang/handlebars.js/commit/f0589701698268578199be25285b2ebea1c1e427"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.5.2",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "githubID": "GHSA-2cf5-4w76-r9qv",
                    "summary": "Versions of `handlebars` prior to 3.0.8 or 4.5.2 are vulnerable to Arbitrary Code Execution. The package's lookup helper fails to properly validate templates, allowing attackers to submit templates that execute arbitrary JavaScript in the system. It can be used to run arbitrary code in a server processing Handlebars templates or on a victim's browser (effectively serving as Cross-Site Scripting).\n\nThe following template can be used to demonstrate the vulnerability:  \n```{{#with \"constructor\"}}\n\t{{#with split as |a|}}\n\t\t{{pop (push \"alert('Vulnerable Handlebars JS');\")}}\n\t\t{{#with (concat (lookup join (slice 0 1)))}}\n\t\t\t{{#each (slice 2 3)}}\n\t\t\t\t{{#with (apply 0 a)}}\n\t\t\t\t\t{{.}}\n\t\t\t\t{{/with}}\n\t\t\t{{/each}}\n\t\t{{/with}}\n\t{{/with}}\n{{/with}}```\n\n\n## Recommendation\n\nUpgrade to version 3.0.8, 4.5.2 or later."
                },
                "info": [
                    "https://github.com/advisories/GHSA-2cf5-4w76-r9qv",
                    "https://www.npmjs.com/advisories/1316"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.5.3",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-20920"
                    ],
                    "githubID": "GHSA-3cqr-58rm-57f8",
                    "summary": "Handlebars before 3.0.8 and 4.x before 4.5.3 is vulnerable to Arbitrary Code Execution. The lookup helper fails to properly validate templates, allowing attackers to submit templates that execute arbitrary JavaScript. This can be used to run arbitrary code on a server processing Handlebars templates or in a victim's browser (effectively serving as XSS)."
                },
                "info": [
                    "https://github.com/advisories/GHSA-3cqr-58rm-57f8",
                    "https://nvd.nist.gov/vuln/detail/CVE-2019-20920"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.5.3",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "githubID": "GHSA-g9r4-xpmj-mj65",
                    "retid": "45",
                    "summary": "Prototype pollution"
                },
                "info": [
                    "https://github.com/advisories/GHSA-g9r4-xpmj-mj65",
                    "https://github.com/wycats/handlebars.js/blob/master/release-notes.md#v453---november-18th-2019"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.5.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-q2c6-c6pm-g3gh",
                    "summary": "Versions of `handlebars` prior to 3.0.8 or 4.5.3 are vulnerable to Arbitrary Code Execution. The package's lookup helper fails to properly validate templates, allowing attackers to submit templates that execute arbitrary JavaScript in the system. It is due to an incomplete fix for a [previous issue](https://www.npmjs.com/advisories/1316). This vulnerability can be used to run arbitrary code in a server processing Handlebars templates or on a victim's browser (effectively serving as Cross-Site Scripting)"
                },
                "info": [
                    "https://github.com/advisories/GHSA-q2c6-c6pm-g3gh",
                    "https://github.com/wycats/handlebars.js/blob/master/release-notes.md#v453---november-18th-2019"
                ],
                "severity": "high"
            },
            {
                "below": "4.6.0",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "issue": "1633",
                    "summary": "Denial of service"
                },
                "info": [
                    "https://github.com/handlebars-lang/handlebars.js/pull/1633"
                ],
                "severity": "medium"
            },
            {
                "below": "4.7.7",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-23383"
                    ],
                    "githubID": "GHSA-765h-qjxv-5f44",
                    "retid": "71",
                    "summary": "Prototype Pollution in handlebars"
                },
                "info": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-23383"
                ],
                "severity": "high"
            },
            {
                "below": "4.7.7",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-23369"
                    ],
                    "githubID": "GHSA-f2jv-r9rf-7988",
                    "summary": "Remote code execution in handlebars when compiling templates"
                },
                "info": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-23369"
                ],
                "severity": "high"
            }
        ]
    },
    "highcharts": {
        "extractors": {
            "filecontent": [
                "product:\"Highcharts\",version:\"([0-9][0-9.a-z_-]+)\"",
                "product=\"Highcharts\"[,;].\\.version=\"([0-9][0-9.a-z_-]+)\""
            ],
            "uri": [
                "highcharts/([0-9][0-9.a-z_-]+)/highcharts(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "6.1.0",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-20801"
                    ],
                    "githubID": "GHSA-xmc8-cjfr-phx3",
                    "summary": "Regular Expression Denial of Service in highcharts"
                },
                "info": [
                    "https://security.snyk.io/vuln/SNYK-JS-HIGHCHARTS-1290057"
                ],
                "severity": "high"
            },
            {
                "below": "7.2.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-gr4j-r575-g665",
                    "summary": "Versions of `highcharts` prior to 7.2.2 or 8.1.1 are vulnerable to Cross-Site Scripting (XSS)"
                },
                "info": [
                    "https://github.com/advisories/GHSA-gr4j-r575-g665",
                    "https://github.com/highcharts/highcharts/issues/13559"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "8.0.0",
                "below": "8.1.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-gr4j-r575-g665",
                    "summary": "Versions of `highcharts` prior to 7.2.2 or 8.1.1 are vulnerable to Cross-Site Scripting (XSS)"
                },
                "info": [
                    "https://github.com/advisories/GHSA-gr4j-r575-g665",
                    "https://github.com/highcharts/highcharts/issues/13559"
                ],
                "severity": "high"
            },
            {
                "below": "9.0.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-29489"
                    ],
                    "githubID": "GHSA-8j65-4pcq-xq95",
                    "summary": "Cross-site Scripting (XSS) and Prototype Pollution in Highcharts < 9.0.0"
                },
                "info": [
                    "https://security.snyk.io/vuln/SNYK-JS-HIGHCHARTS-1290057"
                ],
                "severity": "high"
            }
        ]
    },
    "jPlayer": {
        "bowername": [
            "jPlayer"
        ],
        "extractors": {
            "filecontent": [
                "/\\*!? jPlayer ([0-9][0-9.a-z_-]+) for jQuery",
                "/\\*!?[\n *]+jPlayer Plugin for jQuery (?:.*\n){1,10}[ *]+Version: ([0-9][0-9.a-z_-]+)"
            ],
            "func": [
                "new jQuery.jPlayer().version.script"
            ],
            "hashes": {}
        },
        "npmname": "jplayer",
        "vulnerabilities": [
            {
                "below": "2.2.20",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-1942"
                    ],
                    "release": "2.2.20",
                    "summary": "XSS vulnerabilities in actionscript/Jplayer.as in the Flash SWF component"
                },
                "info": [
                    "http://jplayer.org/latest/release-notes/",
                    "https://nvd.nist.gov/vuln/detail/CVE-2013-1942"
                ],
                "severity": "medium"
            },
            {
                "below": "2.3.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-2022"
                    ],
                    "githubID": "GHSA-3jcq-cwr7-6332",
                    "summary": "XSS vulnerabilities in actionscript/Jplayer.as in the Flash SWF component"
                },
                "info": [
                    "http://jplayer.org/latest/release-notes/",
                    "https://nvd.nist.gov/vuln/detail/CVE-2013-2022"
                ],
                "severity": "medium"
            },
            {
                "below": "2.3.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-2023"
                    ],
                    "release": "2.3.1",
                    "summary": "XSS vulnerability in actionscript/Jplayer.as in the Flash SWF component"
                },
                "info": [
                    "http://jplayer.org/latest/release-notes/",
                    "https://nvd.nist.gov/vuln/detail/CVE-2013-2023"
                ],
                "severity": "medium"
            }
        ]
    },
    "jquery": {
        "bowername": [
            "jQuery"
        ],
        "extractors": {
            "filecontent": [
                "// \\$Id: jquery.js,v ([0-9][0-9.a-z_-]+)",
                "/\\*! jQuery v([0-9][0-9.a-z_-]+)",
                "/\\*!? jQuery v([0-9][0-9.a-z_-]+)",
                "/\\*![\\s]+\\* jQuery JavaScript Library v([0-9][0-9.a-z_-]+)",
                "=\"([0-9][0-9.a-z_-]+)\",.{50,300}(.)\\.fn=(\\2)\\.prototype=\\{jquery:",
                "[^a-z.]jquery:[ ]?\"([0-9][0-9.a-z_-]+)\"",
                "[^a-z]f=\"([0-9][0-9.a-z_-]+)\",.*[^a-z]jquery:f,",
                "[^a-z]m=\"([0-9][0-9.a-z_-]+)\",.*[^a-z]jquery:m,",
                "\\$\\.documentElement,Q=e.jQuery,Z=e\\.\\$,ee=\\{\\},te=\\[\\],ne=\"([0-9][0-9.a-z_-]+)\"",
                "\\* jQuery ([0-9][0-9.a-z_-]+) - New Wave Javascript",
                "\\* jQuery JavaScript Library v([0-9][0-9.a-z_-]+)"
            ],
            "filecontentreplace": [
                "/var [a-z]=[a-z]\\.document,([a-z])=\"([0-9][0-9.a-z_-]+)\",([a-z])=.{130,160};\\3\\.fn=\\3\\.prototype=\\{jquery:\\1/$2/"
            ],
            "filename": [
                "jquery-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "(window.jQuery || window.$ || window.$jq || window.$j).fn.jquery",
                "require('jquery').fn.jquery"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/jquery(\\.min)?\\.js"
            ]
        },
        "npmname": "jquery",
        "vulnerabilities": [
            {
                "below": "1.6.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2011-4969"
                    ],
                    "githubID": "GHSA-579v-mp3v-rrw5",
                    "summary": "XSS with location.hash"
                },
                "info": [
                    "http://research.insecurelabs.org/jquery/test/",
                    "https://bugs.jquery.com/ticket/9521",
                    "https://nvd.nist.gov/vuln/detail/CVE-2011-4969"
                ],
                "severity": "medium"
            },
            {
                "below": "1.9.0b1",
                "cwe": [
                    "CWE-64",
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2012-6708"
                    ],
                    "bug": "11290",
                    "githubID": "GHSA-2pqj-h3vj-pqgw",
                    "summary": "Selector interpreted as HTML"
                },
                "info": [
                    "http://bugs.jquery.com/ticket/11290",
                    "http://research.insecurelabs.org/jquery/test/",
                    "https://nvd.nist.gov/vuln/detail/CVE-2012-6708"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.2.1",
                "below": "1.9.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-7656"
                    ],
                    "githubID": "GHSA-q4m3-2j7h-f7xw",
                    "summary": "Versions of jquery prior to 1.9.0 are vulnerable to Cross-Site Scripting. The load method fails to recognize and remove \"<script>\" HTML tags that contain a whitespace character, i.e: \"</script >\", which results in the enclosed script logic to be executed. This allows attackers to execute arbitrary JavaScript in a victim's browser.\n\n\n## Recommendation\n\nUpgrade to version 1.9.0 or later."
                },
                "info": [
                    "https://github.com/advisories/GHSA-q4m3-2j7h-f7xw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2020-7656",
                    "https://research.insecurelabs.org/jquery/test/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.4.0",
                "below": "1.12.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-9251"
                    ],
                    "githubID": "GHSA-rmxg-73gg-4p98",
                    "issue": "2432",
                    "summary": "3rd party CORS request may execute"
                },
                "info": [
                    "http://blog.jquery.com/2016/01/08/jquery-2-2-and-1-12-released/",
                    "http://research.insecurelabs.org/jquery/test/",
                    "https://bugs.jquery.com/ticket/11974",
                    "https://github.com/advisories/GHSA-rmxg-73gg-4p98",
                    "https://github.com/jquery/jquery/issues/2432",
                    "https://nvd.nist.gov/vuln/detail/CVE-2015-9251"
                ],
                "severity": "medium"
            },
            {
                "below": "2.999.999",
                "cwe": [
                    "CWE-1104"
                ],
                "identifiers": {
                    "issue": "162",
                    "retid": "73",
                    "summary": "jQuery 1.x and 2.x are End-of-Life and no longer receiving security updates"
                },
                "info": [
                    "https://github.com/jquery/jquery.com/issues/162"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "1.12.3",
                "below": "3.0.0-beta1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-9251"
                    ],
                    "githubID": "GHSA-rmxg-73gg-4p98",
                    "issue": "2432",
                    "summary": "3rd party CORS request may execute"
                },
                "info": [
                    "http://blog.jquery.com/2016/01/08/jquery-2-2-and-1-12-released/",
                    "http://research.insecurelabs.org/jquery/test/",
                    "https://bugs.jquery.com/ticket/11974",
                    "https://github.com/advisories/GHSA-rmxg-73gg-4p98",
                    "https://github.com/jquery/jquery/issues/2432",
                    "https://nvd.nist.gov/vuln/detail/CVE-2015-9251"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.0.0-rc.1",
                "below": "3.0.0",
                "cwe": [
                    "CWE-400",
                    "CWE-674"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2016-10707"
                    ],
                    "githubID": "GHSA-mhpp-875w-9cpv",
                    "summary": "Denial of Service in jquery"
                },
                "info": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2016-10707"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.1.4",
                "below": "3.4.0",
                "cwe": [
                    "CWE-1321",
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-11358"
                    ],
                    "PR": "4333",
                    "githubID": "GHSA-6c3j-c64m-qhgq",
                    "summary": "jQuery before 3.4.0, as used in Drupal, Backdrop CMS, and other products, mishandles jQuery.extend(true, {}, ...) because of Object.prototype pollution"
                },
                "info": [
                    "https://blog.jquery.com/2019/04/10/jquery-3-4-0-released/",
                    "https://github.com/jquery/jquery/commit/753d591aea698e57d6db58c9f722cd0808619b1b",
                    "https://nvd.nist.gov/vuln/detail/CVE-2019-11358"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.0.3",
                "below": "3.5.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-11023"
                    ],
                    "githubID": "GHSA-jpcq-cgw6-v4j6",
                    "issue": "4647",
                    "summary": "passing HTML containing <option> elements from untrusted sources - even after sanitizing it - to one of jQuery's DOM manipulation methods (i.e. .html(), .append(), and others) may execute untrusted code."
                },
                "info": [
                    "https://blog.jquery.com/2020/04/10/jquery-3-5-0-released/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "1.2.0",
                "below": "3.5.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-11022"
                    ],
                    "githubID": "GHSA-gxr4-xjj5-5px2",
                    "issue": "4642",
                    "summary": "Regex in its jQuery.htmlPrefilter sometimes may introduce XSS"
                },
                "info": [
                    "https://blog.jquery.com/2020/04/10/jquery-3-5-0-released/"
                ],
                "severity": "medium"
            }
        ]
    },
    "jquery-deparam": {
        "extractors": {
            "hashes": {
                "10a68e5048995351a01b0ad7f322bb755a576a02": "0.5.2",
                "2aae12841f4d00143ffc1effa59fbd058218c29f": "0.4.0",
                "61c9d49ae64331402c3bde766c9dc504ed2ca509": "0.5.3",
                "851bc74dc664aa55130ecc74dd6b1243becc3242": "0.4.1",
                "967942805137f9eb0ae26005d94e8285e2e288a0": "0.3.0",
                "b8f063c860fa3aab266df06b290e7da648f9328d": "0.4.2",
                "fbf2e115feae7ade26788e38ebf338af11a98bb2": "0.1.0"
            }
        },
        "vulnerabilities": [
            {
                "below": "0.5.4",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-20087"
                    ],
                    "githubID": "GHSA-xg68-chx2-253g"
                },
                "info": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-20087"
                ],
                "severity": "high"
            }
        ]
    },
    "jquery-migrate": {
        "extractors": {
            "filecontent": [
                "/\\*!?(?:\n \\*)? jQuery Migrate(?: -)? v([0-9][0-9.a-z_-]+)",
                "\\.migrateVersion ?= ?\"([0-9][0-9.a-z_-]+)\"[\\s\\S]{10,150}(migrateDisablePatches|migrateWarnings|JQMIGRATE)",
                "jQuery\\.migrateVersion ?= ?\"([0-9][0-9.a-z_-]+)\""
            ],
            "filename": [
                "jquery-migrate-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "hashes": {}
        },
        "vulnerabilities": [
            {
                "below": "1.2.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "issue": "36",
                    "release": "jQuery Migrate 1.2.0 Released",
                    "summary": "cross-site-scripting"
                },
                "info": [
                    "http://blog.jquery.com/2013/05/01/jquery-migrate-1-2-0-released/",
                    "https://github.com/jquery/jquery-migrate/issues/36"
                ],
                "severity": "medium"
            },
            {
                "below": "1.2.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "bug": "11290",
                    "summary": "Selector interpreted as HTML"
                },
                "info": [
                    "http://bugs.jquery.com/ticket/11290",
                    "http://research.insecurelabs.org/jquery/test/"
                ],
                "severity": "medium"
            }
        ]
    },
    "jquery-mobile": {
        "bowername": [
            "jquery-mobile",
            "jquery-mobile-bower",
            "jquery-mobile-build",
            "jquery-mobile-dist",
            "jquery-mobile-min"
        ],
        "extractors": {
            "filecontent": [
                "// Version of the jQuery Mobile Framework[\\s]+version: *[\"']([0-9][0-9.a-z_-]+)[\"'],",
                "/\\*!?[\\s*]*jQuery Mobile(?: -)? v?([0-9][0-9.a-z_-]+)"
            ],
            "filename": [
                "jquery.mobile-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "jQuery.mobile.version"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/jquery.mobile(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "1.0.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "osvdb": [
                        "94317"
                    ]
                },
                "info": [
                    "http://osvdb.org/show/osvdb/94317"
                ],
                "severity": "high"
            },
            {
                "below": "1.0RC2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "osvdb": [
                        "94563",
                        "93562",
                        "94316",
                        "94561",
                        "94560"
                    ]
                },
                "info": [
                    "http://osvdb.org/show/osvdb/94316",
                    "http://osvdb.org/show/osvdb/94560",
                    "http://osvdb.org/show/osvdb/94561",
                    "http://osvdb.org/show/osvdb/94562",
                    "http://osvdb.org/show/osvdb/94563"
                ],
                "severity": "high"
            },
            {
                "below": "1.1.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "issue": "4787",
                    "summary": "location.href cross-site scripting"
                },
                "info": [
                    "http://jquerymobile.com/changelog/1.1.2/",
                    "http://jquerymobile.com/changelog/1.2.0/",
                    "https://github.com/jquery/jquery-mobile/issues/4787"
                ],
                "severity": "medium"
            },
            {
                "below": "1.2.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "issue": "4787",
                    "summary": "location.href cross-site scripting"
                },
                "info": [
                    "http://jquerymobile.com/changelog/1.2.0/",
                    "https://github.com/jquery/jquery-mobile/issues/4787"
                ],
                "severity": "medium"
            },
            {
                "below": "1.3.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "gist": "jupenur/e5d0c6f9b58aa81860bf74e010cf1685",
                    "summary": "Endpoint that reflect user input leads to cross site scripting"
                },
                "info": [
                    "https://gist.github.com/jupenur/e5d0c6f9b58aa81860bf74e010cf1685"
                ],
                "severity": "high"
            },
            {
                "below": "100.0.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "blog": "sirdarckcat/unpatched-0day-jquery-mobile-xss",
                    "githubID": "GHSA-fj93-7wm4-8x2g",
                    "summary": "open redirect leads to cross site scripting"
                },
                "info": [
                    "http://sirdarckcat.blogspot.no/2017/02/unpatched-0day-jquery-mobile-xss.html",
                    "https://github.com/jquery/jquery-mobile/issues/8640",
                    "https://snyk.io/vuln/SNYK-JS-JQUERYMOBILE-174599"
                ],
                "severity": "high"
            }
        ]
    },
    "jquery-ui": {
        "bowername": [
            "jquery-ui",
            "jquery.ui"
        ],
        "extractors": {
            "filecontent": [
                "/\\*!? jQuery UI - v([0-9][0-9.a-z_-]+)",
                "/\\*!?[\n *]+jQuery UI ([0-9][0-9.a-z_-]+)"
            ],
            "func": [
                "jQuery.ui.version"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/jquery-ui(\\.min)?\\.js"
            ]
        },
        "npmname": "jquery-ui",
        "vulnerabilities": [
            {
                "below": "1.13.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-41182"
                    ],
                    "githubID": "GHSA-9gj3-hwp5-pmwc",
                    "summary": "XSS in the `altField` option of the Datepicker widget"
                },
                "info": [
                    "https://github.com/jquery/jquery-ui/security/advisories/GHSA-9gj3-hwp5-pmwc",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-41182"
                ],
                "severity": "medium"
            },
            {
                "below": "1.13.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-41184"
                    ],
                    "githubID": "GHSA-gpqq-952q-5327",
                    "summary": "XSS in the `of` option of the `.position()` util"
                },
                "info": [
                    "https://github.com/jquery/jquery-ui/security/advisories/GHSA-gpqq-952q-5327",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-41184"
                ],
                "severity": "medium"
            },
            {
                "below": "1.13.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-41183"
                    ],
                    "bug": "15284",
                    "githubID": "GHSA-j7qv-pgf6-hvh4",
                    "summary": "XSS Vulnerability on text options of jQuery UI datepicker"
                },
                "info": [
                    "https://bugs.jqueryui.com/ticket/15284",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-41183"
                ],
                "severity": "medium"
            },
            {
                "below": "1.13.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-31160"
                    ],
                    "githubID": "GHSA-h6gj-6jjq-h8g9",
                    "issue": "2101",
                    "summary": "XSS when refreshing a checkboxradio with an HTML-like initial text label "
                },
                "info": [
                    "https://github.com/advisories/GHSA-h6gj-6jjq-h8g9",
                    "https://github.com/jquery/jquery-ui/commit/8cc5bae1caa1fcf96bf5862c5646c787020ba3f9",
                    "https://github.com/jquery/jquery-ui/issues/2101",
                    "https://nvd.nist.gov/vuln/detail/CVE-2022-31160"
                ],
                "severity": "medium"
            }
        ]
    },
    "jquery-ui-autocomplete": {
        "bowername": [
            "jquery-ui",
            "jquery.ui"
        ],
        "extractors": {
            "filecontent": [
                "/\\*!? jQuery UI - v([0-9][0-9.a-z_-]+)(.*\n){1,3}.*jquery\\.ui\\.autocomplete\\.js",
                "/\\*!? jQuery UI - v([0-9][0-9.a-z_-]+)(.*\n){1,3}\\* Includes: .* autocomplete\\.js",
                "/\\*!?[\n *]+jQuery UI ([0-9][0-9.a-z_-]+)(.*\n)*.*\\.ui\\.autocomplete",
                "/\\*!?[\n *]+jQuery UI Autocomplete ([0-9][0-9.a-z_-]+)"
            ],
            "func": [
                "jQuery.ui.autocomplete.version"
            ],
            "hashes": {}
        },
        "npmname": "jquery-ui",
        "vulnerabilities": []
    },
    "jquery-ui-dialog": {
        "bowername": [
            "jquery-ui",
            "jquery.ui"
        ],
        "extractors": {
            "filecontent": [
                "/\\*!? jQuery UI - v([0-9][0-9.a-z_-]+)(.*\n){1,3}.*jquery\\.ui\\.dialog\\.js",
                "/\\*!? jQuery UI - v([0-9][0-9.a-z_-]+)(.*\n){1,3}\\* Includes: .* dialog\\.js",
                "/\\*!?[\n *]+jQuery UI ([0-9][0-9.a-z_-]+)(.*\n)*.*\\.ui\\.dialog",
                "/\\*!?[\n *]+jQuery UI Dialog ([0-9][0-9.a-z_-]+)"
            ],
            "func": [
                "jQuery.ui.dialog.version"
            ],
            "hashes": {}
        },
        "npmname": "jquery-ui",
        "vulnerabilities": [
            {
                "atOrAbove": "1.7.0",
                "below": "1.10.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2010-5312"
                    ],
                    "bug": "6016",
                    "githubID": "GHSA-wcm2-9c89-wmfm",
                    "summary": "Title cross-site scripting vulnerability"
                },
                "info": [
                    "http://bugs.jqueryui.com/ticket/6016",
                    "https://nvd.nist.gov/vuln/detail/CVE-2010-5312"
                ],
                "severity": "medium"
            },
            {
                "below": "1.12.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2016-7103"
                    ],
                    "bug": "281",
                    "githubID": "GHSA-hpcf-8vf9-q4gj",
                    "summary": "XSS Vulnerability on closeText option"
                },
                "info": [
                    "https://github.com/jquery/api.jqueryui.com/issues/281",
                    "https://nvd.nist.gov/vuln/detail/CVE-2016-7103",
                    "https://snyk.io/vuln/npm:jquery-ui:20160721"
                ],
                "severity": "medium"
            }
        ]
    },
    "jquery-ui-tooltip": {
        "bowername": [
            "jquery-ui",
            "jquery.ui"
        ],
        "extractors": {
            "filecontent": [
                "/\\*!? jQuery UI - v([0-9][0-9.a-z_-]+)(.*\n){1,3}.*jquery\\.ui\\.tooltip\\.js",
                "/\\*!?[\n *]+jQuery UI ([0-9][0-9.a-z_-]+)(.*\n)*.*\\.ui\\.tooltip",
                "/\\*!?[\n *]+jQuery UI Tooltip ([0-9][0-9.a-z_-]+)"
            ],
            "func": [
                "jQuery.ui.tooltip.version"
            ],
            "hashes": {}
        },
        "npmname": "jquery-ui",
        "vulnerabilities": [
            {
                "atOrAbove": "1.9.2",
                "below": "1.10.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2012-6662"
                    ],
                    "bug": "8859",
                    "githubID": "GHSA-qqxp-xp9v-vvx6",
                    "summary": "Cross-site scripting (XSS) vulnerability in the default content option in jquery.ui.tooltip"
                },
                "info": [
                    "http://bugs.jqueryui.com/ticket/8859",
                    "https://nvd.nist.gov/vuln/detail/CVE-2012-6662"
                ],
                "severity": "medium"
            }
        ]
    },
    "jquery-validation": {
        "bowername": [
            "jquery-validation"
        ],
        "extractors": {
            "filecontent": [
                "/\\*!?(?:\n \\*)?[\\s]*jQuery Validation Plugin -? ?v([0-9][0-9.a-z_-]+)",
                "Original file: /npm/jquery-validation@([0-9][0-9.a-z_-]+)/dist/jquery.validate.js"
            ],
            "filename": [
                "jquery.validat(?:ion|e)-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "jQuery.validation.version"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/jquery.validat(ion|e)(\\.min)?\\.js",
                "/jquery-validation@([0-9][0-9.a-z_-]+)/dist/.*\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "1.19.3",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-21252"
                    ],
                    "githubID": "GHSA-jxwx-85vp-gvwm",
                    "summary": "Regular Expression Denial of Service vulnerability"
                },
                "info": [
                    "https://github.com/jquery-validation/jquery-validation/blob/master/changelog.md#1193--2021-01-09"
                ],
                "severity": "high"
            },
            {
                "below": "1.19.4",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-43306"
                    ],
                    "githubID": "GHSA-j9m2-h2pv-wvph",
                    "issue": "2428",
                    "summary": "ReDoS vulnerability in URL2 validation"
                },
                "info": [
                    "https://github.com/jquery-validation/jquery-validation/blob/master/changelog.md#1194--2022-05-19"
                ],
                "severity": "low"
            },
            {
                "below": "1.19.5",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-31147"
                    ],
                    "githubID": "GHSA-ffmh-x56j-9rc3",
                    "summary": "ReDoS vulnerability in url and URL2 validation"
                },
                "info": [
                    "https://github.com/advisories/GHSA-ffmh-x56j-9rc3",
                    "https://github.com/jquery-validation/jquery-validation/commit/5bbd80d27fc6b607d2f7f106c89522051a9fb0dd"
                ],
                "severity": "high"
            },
            {
                "below": "1.20.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "PR": "2462",
                    "summary": "Potential XSS via showLabel"
                },
                "info": [
                    "https://github.com/jquery-validation/jquery-validation/blob/master/changelog.md#1200--2023-10-10"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "1.20.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-3573"
                    ],
                    "githubID": "GHSA-rrj2-ph5q-jxw2",
                    "summary": "jquery-validation vulnerable to Cross-site Scripting"
                },
                "info": [
                    "https://github.com/advisories/GHSA-rrj2-ph5q-jxw2",
                    "https://github.com/jquery-validation/jquery-validation",
                    "https://github.com/jquery-validation/jquery-validation/commit/7a490d8f39bd988027568ddcf51755e1f4688902",
                    "https://github.com/jquery-validation/jquery-validation/pull/2462",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-3573",
                    "https://security.snyk.io/vuln/SNYK-JS-JQUERYVALIDATION-5952285"
                ],
                "severity": "medium"
            }
        ]
    },
    "jquery.datatables": {
        "extractors": {
            "filecontent": [
                ".\\.version=\"([0-9][0-9.a-z_-]+)\";[\\s]*.\\.settings=\\[\\];[\\s]*.\\.models=\\{[\\s]*\\};[\\s]*.\\.models.oSearch",
                "/\\*! DataTables ([0-9][0-9.a-z_-]+)",
                "http://www.datatables.net\n +DataTables ([0-9][0-9.a-z_-]+)"
            ],
            "filename": [
                "jquery.dataTables-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "DataTable && DataTable.version"
            ],
            "uri": [
                "/([0-9][0-9.a-z_-]+)/(js/)?jquery.dataTables(.min)?.js"
            ]
        },
        "npmname": "datatables.net",
        "vulnerabilities": [
            {
                "below": "1.10.10",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-6584"
                    ],
                    "summary": "XSS"
                },
                "info": [
                    "https://github.com/DataTables/DataTablesSrc/commit/ccf86dc5982bd8e16d",
                    "https://github.com/advisories/GHSA-4mv4-gmmf-q382",
                    "https://www.invicti.com/web-applications-advisories/cve-2015-6384-xss-vulnerability-identified-in-datatables/"
                ],
                "severity": "high"
            },
            {
                "below": "1.10.22",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-28458"
                    ],
                    "githubID": "GHSA-m7j4-fhg6-xf5v",
                    "summary": "datatables.net vulnerable to Prototype Pollution due to incomplete fix"
                },
                "info": [
                    "https://github.com/advisories/GHSA-m7j4-fhg6-xf5v"
                ],
                "severity": "high"
            },
            {
                "below": "1.10.22",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "retid": "4",
                    "summary": "prototype pollution"
                },
                "info": [
                    "https://cdn.datatables.net/1.10.22/"
                ],
                "severity": "medium"
            },
            {
                "below": "1.10.23",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "retid": "3",
                    "summary": "prototype pollution"
                },
                "info": [
                    "https://cdn.datatables.net/1.10.23/",
                    "https://github.com/DataTables/DataTablesSrc/commit/a51cbe99fd3d02aa5582f97d4af1615d11a1ea03"
                ],
                "severity": "high"
            },
            {
                "below": "1.11.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "2",
                    "summary": "possible XSS"
                },
                "info": [
                    "https://cdn.datatables.net/1.11.3/",
                    "https://github.com/DataTables/Dist-DataTables/commit/59a8d3f8a3c1138ab08704e783bc52bfe88d7c9b"
                ],
                "severity": "low"
            },
            {
                "below": "1.11.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-23445"
                    ],
                    "githubID": "GHSA-h73q-5wmj-q8pj",
                    "summary": "Cross site scripting in datatables.net"
                },
                "info": [
                    "https://github.com/advisories/GHSA-h73q-5wmj-q8pj"
                ],
                "severity": "medium"
            }
        ]
    },
    "jquery.prettyPhoto": {
        "basePurl": "pkg:github/scaron/prettyphoto",
        "bowername": [
            "jquery-prettyPhoto"
        ],
        "extractors": {
            "filecontent": [
                "/\\*[\r\n -]+Class: prettyPhoto(?:.*\n){1,3}[ ]*Version: ([0-9][0-9.a-z_-]+)",
                "\\.prettyPhoto[ ]?=[ ]?\\{version:[ ]?(?:'|\")([0-9][0-9.a-z_-]+)(?:'|\")\\}"
            ],
            "func": [
                "jQuery.prettyPhoto.version"
            ],
            "hashes": {},
            "uri": [
                "/prettyPhoto/([0-9][0-9.a-z_-]+)/js/jquery\\.prettyPhoto(\\.min?)\\.js",
                "/prettyphoto@([0-9][0-9.a-z_-]+)/js/jquery\\.prettyPhoto\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "3.1.5",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-6837"
                    ]
                },
                "info": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2013-6837"
                ],
                "severity": "medium"
            },
            {
                "below": "3.1.6",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "issue": "149"
                },
                "info": [
                    "https://blog.anantshri.info/forgotten_disclosure_dom_xss_prettyphoto",
                    "https://github.com/scaron/prettyphoto/issues/149"
                ],
                "severity": "high"
            }
        ]
    },
    "jquery.terminal": {
        "extractors": {
            "filecontent": [
                "\\$\\.terminal=\\{version:\"([0-9][0-9.a-z_-]+)\"",
                "version ([0-9][0-9.a-z_-]+)[\\s]+\\*[\\s]+\\* This file is part of jQuery Terminal."
            ],
            "uri": [
                "/jquery.terminal[@/]([0-9][0-9.a-z_-]+)/"
            ]
        },
        "vulnerabilities": [
            {
                "below": "1.21.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-2hwp-g4g7-mwwj",
                    "summary": "Reflected Cross-Site Scripting in jquery.terminal"
                },
                "info": [
                    "https://github.com/jcubic/jquery.terminal/commit/c8b7727d21960031b62a4ef1ed52f3c634046211",
                    "https://www.npmjs.com/advisories/769"
                ],
                "severity": "medium"
            },
            {
                "below": "2.31.1",
                "cwe": [
                    "CWE-79",
                    "CWE-80"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-43862"
                    ],
                    "githubID": "GHSA-x9r5-jxvq-4387",
                    "summary": "jquery.terminal self XSS on user input"
                },
                "info": [
                    "https://github.com/jcubic/jquery.terminal/security/advisories/GHSA-x9r5-jxvq-4387",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-43862"
                ],
                "severity": "low"
            }
        ]
    },
    "jszip": {
        "extractors": {
            "filecontent": [
                "/\\*![\\s]+JSZip v([0-9][0-9.a-z_-]+) "
            ],
            "filename": [
                "jszip-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "JSZip && JSZip.version"
            ],
            "uri": [
                "/jszip[/@]([0-9][0-9.a-z_-]+)/.*\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "2.7.0",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-23413"
                    ],
                    "githubID": "GHSA-jg8v-48h5-wgxg",
                    "summary": "Prototype Pollution"
                },
                "info": [
                    "https://github.com/advisories/GHSA-jg8v-48h5-wgxg",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-23413",
                    "https://security.snyk.io/vuln/SNYK-JS-JSZIP-1251497"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.0.0",
                "below": "3.7.0",
                "cwe": [
                    "CWE-1321"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-23413"
                    ],
                    "githubID": "GHSA-jg8v-48h5-wgxg",
                    "summary": "Prototype Pollution"
                },
                "info": [
                    "https://github.com/advisories/GHSA-jg8v-48h5-wgxg",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-23413",
                    "https://security.snyk.io/vuln/SNYK-JS-JSZIP-1251497"
                ],
                "severity": "medium"
            },
            {
                "below": "3.8.0",
                "cwe": [
                    "CWE-22"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-48285"
                    ],
                    "githubID": "GHSA-36fh-84j7-cv5h",
                    "retid": "5",
                    "summary": "Santize filenames when files are loaded with loadAsync, to avoid \u201czip slip\u201d attacks."
                },
                "info": [
                    "https://stuk.github.io/jszip/CHANGES.html"
                ],
                "severity": "medium"
            }
        ]
    },
    "knockout": {
        "extractors": {
            "filecontent": [
                "(?:\\*|//) Knockout JavaScript library v([0-9][0-9.a-z_-]+)"
            ],
            "filename": [
                "knockout-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "ko.version"
            ],
            "hashes": {},
            "uri": [
                "/knockout/([0-9][0-9.a-z_-]+)/knockout(-[a-z.]+)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "3.5.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-14862"
                    ],
                    "githubID": "GHSA-vcjj-xf2r-mwvc",
                    "issue": "1244",
                    "summary": "XSS injection point in attr name binding for browser IE7 and older"
                },
                "info": [
                    "https://github.com/knockout/knockout/issues/1244"
                ],
                "severity": "medium"
            }
        ]
    },
    "lodash": {
        "extractors": {
            "filecontent": [
                "/\\*[\\s*!]+(?:@license)?[\\s*]+(?:Lo-Dash|lodash|Lodash) v?([0-9][0-9.a-z_-]+) <",
                "/\\*[\\s*!]+(?:@license)?[\\s*]+(?:Lo-Dash|lodash|Lodash) v?([0-9][0-9.a-z_-]+) lodash.com/license",
                "/\\*[\\s*!]+(?:@license)?[\\s*]+(?:Lo-Dash|lodash|Lodash) v?([0-9][0-9.a-z_-]+)[\\s\\S]{1,200}Build: `lodash modern -o",
                "/\\*[\\s*]+@license[\\s*]+(?:Lo-Dash|lodhash|Lodash)[\\s\\S]{1,500}var VERSION *= *['\"]([0-9][0-9.a-z_-]+)['\"]",
                "=\"([0-9][0-9.a-z_-]+)\"[\\s\\S]{1,300}__lodash_hash_undefined__",
                "var VERSION=\"([0-9][0-9.a-z_-]+)\";var BIND_FLAG=1,BIND_KEY_FLAG=2,CURRY_BOUND_FLAG=4,CURRY_FLAG=8"
            ],
            "uri": [
                "/([0-9][0-9.a-z_-]+)/lodash(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "4.17.5",
                "cwe": [
                    "CWE-471",
                    "CWE-1321"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-3721"
                    ],
                    "githubID": "GHSA-fvqr-27wr-82fm",
                    "summary": "Prototype Pollution in lodash"
                },
                "info": [
                    "https://github.com/advisories/GHSA-fvqr-27wr-82fm",
                    "https://github.com/lodash/lodash/commit/d8e069cc3410082e44eb18fcf8e7f3d08ebe1d4a",
                    "https://hackerone.com/reports/310443",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-3721",
                    "https://security.netapp.com/advisory/ntap-20190919-0004/",
                    "https://www.npmjs.com/advisories/577"
                ],
                "severity": "medium"
            },
            {
                "below": "4.17.11",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-16487"
                    ],
                    "githubID": "GHSA-4xc9-xhrj-v574",
                    "summary": "Prototype Pollution in lodash"
                },
                "info": [
                    "https://github.com/advisories/GHSA-4xc9-xhrj-v574",
                    "https://github.com/lodash/lodash/commit/90e6199a161b6445b01454517b40ef65ebecd2ad",
                    "https://hackerone.com/reports/380873",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-16487",
                    "https://security.netapp.com/advisory/ntap-20190919-0004/",
                    "https://www.npmjs.com/advisories/782"
                ],
                "severity": "high"
            },
            {
                "below": "4.17.11",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-1010266"
                    ],
                    "githubID": "GHSA-x5rq-j2xg-h7qm",
                    "summary": "Regular Expression Denial of Service (ReDoS) in lodash"
                },
                "info": [
                    "https://github.com/advisories/GHSA-x5rq-j2xg-h7qm",
                    "https://github.com/lodash/lodash/commit/5c08f18d365b64063bfbfa686cbb97cdd6267347",
                    "https://github.com/lodash/lodash/issues/3359",
                    "https://github.com/lodash/lodash/wiki/Changelog",
                    "https://nvd.nist.gov/vuln/detail/CVE-2019-1010266",
                    "https://security.netapp.com/advisory/ntap-20190919-0004/",
                    "https://snyk.io/vuln/SNYK-JS-LODASH-73639"
                ],
                "severity": "medium"
            },
            {
                "below": "4.17.12",
                "cwe": [
                    "CWE-1321",
                    "CWE-20"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-10744"
                    ],
                    "githubID": "GHSA-jf85-cpcp-j695",
                    "summary": "Prototype Pollution in lodash"
                },
                "info": [
                    "https://access.redhat.com/errata/RHSA-2019:3024",
                    "https://github.com/advisories/GHSA-jf85-cpcp-j695",
                    "https://github.com/lodash/lodash/pull/4336",
                    "https://nvd.nist.gov/vuln/detail/CVE-2019-10744",
                    "https://security.netapp.com/advisory/ntap-20191004-0005/",
                    "https://snyk.io/vuln/SNYK-JS-LODASH-450202",
                    "https://support.f5.com/csp/article/K47105354?utm_source=f5support&amp;utm_medium=RSS",
                    "https://www.npmjs.com/advisories/1065",
                    "https://www.oracle.com/security-alerts/cpujan2021.html",
                    "https://www.oracle.com/security-alerts/cpuoct2020.html"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "3.7.0",
                "below": "4.17.19",
                "cwe": [
                    "CWE-1321",
                    "CWE-770"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-8203"
                    ],
                    "githubID": "GHSA-p6mc-m468-83gw",
                    "summary": "Prototype Pollution in lodash"
                },
                "info": [
                    "https://github.com/advisories/GHSA-p6mc-m468-83gw",
                    "https://github.com/github/advisory-database/pull/2884",
                    "https://github.com/lodash/lodash",
                    "https://github.com/lodash/lodash/commit/c84fe82760fb2d3e03a63379b297a1cc1a2fce12",
                    "https://github.com/lodash/lodash/issues/4744",
                    "https://github.com/lodash/lodash/issues/4874",
                    "https://github.com/lodash/lodash/wiki/Changelog#v41719",
                    "https://hackerone.com/reports/712065",
                    "https://hackerone.com/reports/864701",
                    "https://nvd.nist.gov/vuln/detail/CVE-2020-8203",
                    "https://web.archive.org/web/20210914001339/https://github.com/lodash/lodash/issues/4744"
                ],
                "severity": "high"
            },
            {
                "below": "4.17.21",
                "cwe": [
                    "CWE-1333",
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-28500"
                    ],
                    "githubID": "GHSA-29mw-wpgm-hmr9",
                    "summary": "Regular Expression Denial of Service (ReDoS) in lodash"
                },
                "info": [
                    "https://cert-portal.siemens.com/productcert/pdf/ssa-637483.pdf",
                    "https://github.com/advisories/GHSA-29mw-wpgm-hmr9",
                    "https://github.com/lodash/lodash",
                    "https://github.com/lodash/lodash/blob/npm/trimEnd.js%23L8",
                    "https://github.com/lodash/lodash/commit/c4847ebe7d14540bb28a8b932a9ce1b9ecbfee1a",
                    "https://github.com/lodash/lodash/pull/5065",
                    "https://github.com/lodash/lodash/pull/5065/commits/02906b8191d3c100c193fe6f7b27d1c40f200bb7",
                    "https://nvd.nist.gov/vuln/detail/CVE-2020-28500",
                    "https://security.netapp.com/advisory/ntap-20210312-0006/",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGFUJIONWEBJARS-1074896",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARS-1074894",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSBOWER-1074892",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSBOWERGITHUBLODASH-1074895",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSNPM-1074893",
                    "https://snyk.io/vuln/SNYK-JS-LODASH-1018905",
                    "https://www.oracle.com//security-alerts/cpujul2021.html",
                    "https://www.oracle.com/security-alerts/cpujan2022.html",
                    "https://www.oracle.com/security-alerts/cpujul2022.html",
                    "https://www.oracle.com/security-alerts/cpuoct2021.html"
                ],
                "severity": "medium"
            },
            {
                "below": "4.17.21",
                "cwe": [
                    "CWE-77",
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-23337"
                    ],
                    "githubID": "GHSA-35jh-r3h4-6jhm",
                    "summary": "Command Injection in lodash"
                },
                "info": [
                    "https://cert-portal.siemens.com/productcert/pdf/ssa-637483.pdf",
                    "https://github.com/advisories/GHSA-35jh-r3h4-6jhm",
                    "https://github.com/lodash/lodash",
                    "https://github.com/lodash/lodash/blob/ddfd9b11a0126db2302cb70ec9973b66baec0975/lodash.js#L14851",
                    "https://github.com/lodash/lodash/blob/ddfd9b11a0126db2302cb70ec9973b66baec0975/lodash.js%23L14851",
                    "https://github.com/lodash/lodash/commit/3469357cff396a26c363f8c1b5a91dde28ba4b1c",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-23337",
                    "https://security.netapp.com/advisory/ntap-20210312-0006/",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGFUJIONWEBJARS-1074932",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARS-1074930",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSBOWER-1074928",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSBOWERGITHUBLODASH-1074931",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSNPM-1074929",
                    "https://snyk.io/vuln/SNYK-JS-LODASH-1040724",
                    "https://www.oracle.com//security-alerts/cpujul2021.html",
                    "https://www.oracle.com/security-alerts/cpujan2022.html",
                    "https://www.oracle.com/security-alerts/cpujul2022.html",
                    "https://www.oracle.com/security-alerts/cpuoct2021.html"
                ],
                "severity": "high"
            }
        ]
    },
    "markdown-it": {
        "extractors": {
            "filecontent": [
                "/\\*! markdown-it(?:-ins)? ([0-9][0-9.a-z_-]+)"
            ],
            "filename": [
                "markdown-it-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [],
            "uri": [
                "/markdown-it[/@]([0-9][0-9.a-z_-]+)/?.*\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "3.0.0",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-10005"
                    ],
                    "githubID": "GHSA-j5p7-jf4q-742q",
                    "summary": "Cross-site Scripting (XSS)"
                },
                "info": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2015-10005"
                ],
                "severity": "high"
            },
            {
                "below": "4.1.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-3295"
                    ],
                    "summary": "Cross-site Scripting (XSS)"
                },
                "info": [
                    "https://cve.mitre.org/cgi-bin/cvename.cgi?name=2015-3295",
                    "https://github.com/markdown-it/markdown-it/blob/master/CHANGELOG.md",
                    "https://security.snyk.io/vuln/npm:markdown-it:20160912"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "4.0.0",
                "below": "4.3.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "7",
                    "summary": "Cross-site Scripting (XSS)"
                },
                "info": [
                    "https://github.com/markdown-it/markdown-it/blob/master/CHANGELOG.md",
                    "https://security.snyk.io/vuln/npm:markdown-it:20150702"
                ],
                "severity": "medium"
            },
            {
                "below": "10.0.0",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "retid": "6",
                    "summary": "Regular Expression Denial of Service (ReDoS)"
                },
                "info": [
                    "https://github.com/markdown-it/markdown-it/blob/master/CHANGELOG.md",
                    "https://security.snyk.io/vuln/SNYK-JS-MARKDOWNIT-459438"
                ],
                "severity": "medium"
            },
            {
                "below": "12.3.2",
                "cwe": [
                    "CWE-1333",
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-21670"
                    ],
                    "githubID": "GHSA-6vfc-qv3f-vr6c",
                    "summary": "Regular Expression Denial of Service (ReDoS)"
                },
                "info": [
                    "https://github.com/markdown-it/markdown-it/blob/master/CHANGELOG.md",
                    "https://nvd.nist.gov/vuln/detail/CVE-2022-21670",
                    "https://security.snyk.io/vuln/SNYK-JS-MARKDOWNIT-2331914"
                ],
                "severity": "medium"
            },
            {
                "below": "13.0.2",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "issue": "957",
                    "summary": "Fixed crash/infinite loop caused by linkify inline rule"
                },
                "info": [
                    "https://github.com/markdown-it/markdown-it/compare/13.0.1...13.0.2",
                    "https://github.com/markdown-it/markdown-it/issues/957"
                ],
                "severity": "medium"
            }
        ]
    },
    "mathjax": {
        "extractors": {
            "filecontent": [
                "MathJax.{0,100}.\\.VERSION=void 0,.\\.VERSION=\"([0-9][0-9.a-z_-]+)\"",
                "MathJax\\.version=\"([0-9][0-9.a-z_-]+)\";",
                "\\.MathJax=\\{version:\"([0-9][0-9.a-z_-]+)\"",
                "\\.MathJax\\.config\\.startup;{10,100}.\\.VERSION=\"([0-9][0-9.a-z_-]+)\""
            ],
            "func": [
                "MathJax.version"
            ],
            "uri": [
                "/mathjax/([0-9][0-9.a-z_-]+)/",
                "/mathjax@([0-9][0-9.a-z_-]+)/"
            ]
        },
        "vulnerabilities": [
            {
                "atOrAbove": "0",
                "below": "2.7.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-1999024"
                    ],
                    "githubID": "GHSA-3c48-6pcv-88rm",
                    "summary": "Macro in MathJax running untrusted Javascript within a web browser"
                },
                "info": [
                    "https://blog.bentkowski.info/2018/06/xss-in-google-colaboratory-csp-bypass.html",
                    "https://github.com/advisories/GHSA-3c48-6pcv-88rm",
                    "https://github.com/mathjax/MathJax",
                    "https://github.com/mathjax/MathJax/commit/a55da396c18cafb767a26aa9ad96f6f4199852f1",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-1999024"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "2.7.10",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-39663"
                    ],
                    "githubID": "GHSA-v638-q856-grg8",
                    "summary": "MathJax Regular expression Denial of Service (ReDoS)"
                },
                "info": [
                    "https://github.com/advisories/GHSA-v638-q856-grg8",
                    "https://github.com/mathjax/MathJax/issues/3074",
                    "https://nvd.nist.gov/vuln/detail/CVE-2023-39663"
                ],
                "severity": "high"
            }
        ]
    },
    "moment.js": {
        "basePurl": "pkg:npm/moment",
        "bowername": [
            "moment",
            "momentjs"
        ],
        "extractors": {
            "filecontent": [
                "// Moment.js is freely distributable under the terms of the MIT license.[\\s]+//[\\s]+// Version ([0-9][0-9.a-z_-]+)",
                "//!? moment.js(?:[\n\r]+)//!? version : ([0-9][0-9.a-z_-]+)",
                "/\\* Moment.js +\\| +version : ([0-9][0-9.a-z_-]+) \\|",
                "=\"([0-9][0-9.a-z_-]+)\".{300,1000}Years:31536e6.{60,80}\\.isMoment",
                "\\.isMoment\\(.{50,400}_isUTC.{50,400}=\"([0-9][0-9.a-z_-]+)\"",
                "\\.version=\"([0-9][0-9.a-z_-]+)\".{20,300}duration.{2,100}\\.isMoment=",
                "\\.version=\"([0-9][0-9.a-z_-]+)\".{20,60}\"isBefore\".{20,60}\"isAfter\".{200,500}\\.isMoment="
            ],
            "filename": [
                "moment(?:-|\\.)([0-9][0-9.a-z_-]+)(?:-min)?\\.js"
            ],
            "func": [
                "moment.version"
            ],
            "uri": [
                "/moment\\.js/([0-9][0-9.a-z_-]+)/moment(.min)?\\.js"
            ]
        },
        "npmname": "moment",
        "vulnerabilities": [
            {
                "below": "2.11.2",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2016-4055"
                    ],
                    "githubID": "GHSA-87vv-r9j6-g5qv",
                    "issue": "2936",
                    "summary": "reDOS - regular expression denial of service"
                },
                "info": [
                    "https://github.com/moment/moment/issues/2936"
                ],
                "severity": "medium"
            },
            {
                "below": "2.15.2",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "retid": "22",
                    "summary": "Regular Expression Denial of Service (ReDoS)"
                },
                "info": [
                    "https://security.snyk.io/vuln/npm:moment:20161019"
                ],
                "severity": "medium"
            },
            {
                "below": "2.19.3",
                "cwe": [
                    "CWE-1333",
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2017-18214"
                    ],
                    "githubID": "GHSA-446m-mv8f-q348",
                    "summary": "Regular Expression Denial of Service (ReDoS)"
                },
                "info": [
                    "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2017-18214",
                    "https://github.com/moment/moment/issues/4163",
                    "https://security.snyk.io/vuln/npm:moment:20170905"
                ],
                "severity": "high"
            },
            {
                "below": "2.29.2",
                "cwe": [
                    "CWE-22",
                    "CWE-27"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-24785"
                    ],
                    "githubID": "GHSA-8hfj-j24r-96c4",
                    "summary": "This vulnerability impacts npm (server) users of moment.js, especially if user provided locale string, eg fr is directly used to switch moment locale."
                },
                "info": [
                    "https://github.com/moment/moment/security/advisories/GHSA-8hfj-j24r-96c4"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "2.18.0",
                "below": "2.29.4",
                "cwe": [
                    "CWE-1333",
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-31129"
                    ],
                    "githubID": "GHSA-wc69-rhjr-hc9g",
                    "summary": "Regular Expression Denial of Service (ReDoS), Affecting moment package, versions >=2.18.0 <2.29.4"
                },
                "info": [
                    "https://github.com/moment/moment/security/advisories/GHSA-wc69-rhjr-hc9g",
                    "https://security.snyk.io/vuln/SNYK-JS-MOMENT-2944238"
                ],
                "severity": "high"
            }
        ]
    },
    "mustache.js": {
        "basePurl": "pkg:npm/mustache",
        "bowername": [
            "mustache",
            "mustache.js"
        ],
        "extractors": {
            "filecontent": [
                "[^a-z]mustache.version[ ]?=[ ]?(?:'|\")([0-9][0-9.a-z_-]+)(?:'|\")",
                "exports.name[ ]?=[ ]?\"mustache.js\";[\n ]*exports.version[ ]?=[ ]?(?:'|\")([0-9][0-9.a-z_-]+)(?:'|\");",
                "name:\"mustache.js\",version:\"([0-9][0-9.a-z_-]+)\"",
                "name=\"mustache.js\"[;,].\\.version=\"([0-9][0-9.a-z_-]+)\""
            ],
            "filename": [
                "mustache(?:js)?-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "Mustache.version"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/mustache(\\.min)?\\.js"
            ]
        },
        "npmname": "mustache",
        "vulnerabilities": [
            {
                "below": "0.3.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "bug": "112",
                    "summary": "execution of arbitrary javascript"
                },
                "info": [
                    "https://github.com/janl/mustache.js/issues/112"
                ],
                "severity": "high"
            },
            {
                "below": "2.2.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2015-8862"
                    ],
                    "PR": "530",
                    "githubID": "GHSA-w3w8-37jv-2c58",
                    "summary": "weakness in HTML escaping"
                },
                "info": [
                    "https://github.com/janl/mustache.js/pull/530",
                    "https://github.com/janl/mustache.js/releases/tag/v2.2.1"
                ],
                "severity": "high"
            }
        ]
    },
    "nextjs": {
        "extractors": {
            "filecontent": [
                "=\"([0-9][0-9.a-z_-]+)\"[\\s\\S]{10,100}Component[\\s\\S]{1,10}componentDidCatch[\\s\\S]{10,30}componentDidMount",
                "document\\.getElementById\\(\"__NEXT_DATA__\"\\)\\.textContent\\);window\\.__NEXT_DATA__=.;.\\.version=\"([0-9][0-9.a-z_-]+)\"",
                "version=\"([0-9][0-9.a-z_-]+)\".{1,1500}document\\.getElementById\\(\"__NEXT_DATA__\"\\)\\.textContent"
            ],
            "func": [
                "next && next.version"
            ]
        },
        "npmname": "next",
        "vulnerabilities": [
            {
                "atOrAbove": "1.0.0",
                "below": "2.4.1",
                "cwe": [
                    "CWE-22"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2017-16877"
                    ],
                    "githubID": "GHSA-3f5c-4qxj-vmpf",
                    "summary": "Next.js Directory Traversal Vulnerability"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-3f5c-4qxj-vmpf"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.0.0",
                "below": "4.2.3",
                "cwe": [
                    "CWE-22"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6184"
                    ],
                    "githubID": "GHSA-m34x-wgrh-g897",
                    "summary": "Directory traversal vulnerability in Next.js"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-m34x-wgrh-g897"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0.9.9",
                "below": "5.1.0",
                "cwe": [
                    "CWE-20"
                ],
                "identifiers": {
                    "githubID": "GHSA-5vj8-3v2h-h38v",
                    "summary": "Remote Code Execution in next"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-5vj8-3v2h-h38v"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "7.0.0",
                "below": "7.0.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-18282"
                    ],
                    "githubID": "GHSA-qw96-mm2g-c8m7",
                    "summary": "Next.js has cross site scripting (XSS) vulnerability via the 404 or 500 /_error page"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-qw96-mm2g-c8m7"
                ],
                "severity": "medium"
            },
            {
                "below": "9.3.2",
                "cwe": [
                    "CWE-23"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-5284"
                    ],
                    "githubID": "GHSA-fq77-7p7r-83rj",
                    "summary": "Directory Traversal in Next.js"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-fq77-7p7r-83rj"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "9.5.0",
                "below": "9.5.4",
                "cwe": [
                    "CWE-601"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-15242"
                    ],
                    "githubID": "GHSA-x56p-c8cg-q435",
                    "summary": "Open Redirect in Next.js"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-x56p-c8cg-q435"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0.9.9",
                "below": "11.1.0",
                "cwe": [
                    "CWE-601"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-37699"
                    ],
                    "githubID": "GHSA-vxf5-wxwp-m7g9",
                    "summary": "Open Redirect in Next.js"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-vxf5-wxwp-m7g9"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "10.0.0",
                "below": "11.1.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-39178"
                    ],
                    "githubID": "GHSA-9gr3-7897-pp7m",
                    "summary": "XSS in Image Optimization API"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-9gr3-7897-pp7m"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0.9.9",
                "below": "11.1.3",
                "cwe": [
                    "CWE-20"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-43803"
                    ],
                    "githubID": "GHSA-25mp-g6fv-mqxx",
                    "summary": "Unexpected server crash in Next.js versions"
                },
                "info": [
                    "https://github.com/advisories/GHSA-25mp-g6fv-mqxx",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-25mp-g6fv-mqxx"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "12.0.0",
                "below": "12.0.5",
                "cwe": [
                    "CWE-20"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-43803"
                    ],
                    "githubID": "GHSA-25mp-g6fv-mqxx",
                    "summary": "Unexpected server crash in Next.js versions"
                },
                "info": [
                    "https://github.com/advisories/GHSA-25mp-g6fv-mqxx",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-25mp-g6fv-mqxx"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "12.0.0",
                "below": "12.0.9",
                "cwe": [
                    "CWE-20",
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-21721"
                    ],
                    "githubID": "GHSA-wr66-vrwm-5g5x",
                    "summary": "DOS Vulnerability for self-hosted next.js apps"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-wr66-vrwm-5g5x"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "10.0.0",
                "below": "12.1.0",
                "cwe": [
                    "CWE-451"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-23646"
                    ],
                    "githubID": "GHSA-fmvm-x8mv-47mj",
                    "summary": "Improper CSP in Image Optimization API"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-fmvm-x8mv-47mj"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "12.2.3",
                "below": "12.2.4",
                "cwe": [
                    "CWE-248",
                    "CWE-754"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-36046"
                    ],
                    "githubID": "GHSA-wff4-fpwg-qqv3",
                    "summary": "Unexpected server crash in Next.js"
                },
                "info": [
                    "https://github.com/vercel/next.js/security/advisories/GHSA-wff4-fpwg-qqv3"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "11.1.4",
                "below": "12.3.5",
                "cwe": [
                    "CWE-285"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-29927"
                    ],
                    "githubID": "GHSA-f82v-jwr5-mffw",
                    "summary": "Authorization Bypass in Next.js Middleware"
                },
                "info": [
                    "http://www.openwall.com/lists/oss-security/2025/03/23/3",
                    "http://www.openwall.com/lists/oss-security/2025/03/23/4",
                    "https://github.com/advisories/GHSA-f82v-jwr5-mffw",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/commit/52a078da3884efe6501613c7834a3d02a91676d2",
                    "https://github.com/vercel/next.js/commit/5fd3ae8f8542677c6294f32d18022731eab6fe48",
                    "https://github.com/vercel/next.js/releases/tag/v12.3.5",
                    "https://github.com/vercel/next.js/releases/tag/v13.5.9",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-f82v-jwr5-mffw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-29927",
                    "https://security.netapp.com/advisory/ntap-20250328-0002",
                    "https://vercel.com/changelog/vercel-firewall-proactively-protects-against-vulnerability-with-middleware"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "12.3.5",
                "below": "12.3.6",
                "cwe": [
                    "CWE-200"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-30218"
                    ],
                    "githubID": "GHSA-223j-4rm8-mrmf",
                    "summary": "Next.js may leak x-middleware-subrequest-id to external hosts"
                },
                "info": [
                    "https://github.com/advisories/GHSA-223j-4rm8-mrmf",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-223j-4rm8-mrmf",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-30218",
                    "https://vercel.com/changelog/cve-2025-30218-5DREmEH765PoeAsrNNQj3O"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "0.9.9",
                "below": "13.4.20-canary.13",
                "cwe": [
                    "CWE-525"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-46298"
                    ],
                    "githubID": "GHSA-c59h-r6p8-q9wc",
                    "summary": "Next.js missing cache-control header may lead to CDN caching empty reply"
                },
                "info": [
                    "https://github.com/advisories/GHSA-c59h-r6p8-q9wc"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "13.3.1",
                "below": "13.5.0",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-39693"
                    ],
                    "githubID": "GHSA-fq54-2j52-jc42",
                    "summary": "Next.js Denial of Service (DoS) condition"
                },
                "info": [
                    "https://github.com/advisories/GHSA-fq54-2j52-jc42",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-fq54-2j52-jc42",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-39693"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "13.4.0",
                "below": "13.5.1",
                "cwe": [
                    "CWE-444"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-34350"
                    ],
                    "githubID": "GHSA-77r5-gw3j-2mpf",
                    "summary": "Next.js Vulnerable to HTTP Request Smuggling"
                },
                "info": [
                    "https://github.com/advisories/GHSA-77r5-gw3j-2mpf",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/commit/44eba020c615f0d9efe431f84ada67b81576f3f5",
                    "https://github.com/vercel/next.js/compare/v13.5.0...v13.5.1",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-77r5-gw3j-2mpf",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-34350"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "13.5.1",
                "below": "13.5.7",
                "cwe": [
                    "CWE-349",
                    "CWE-639"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-46982"
                    ],
                    "githubID": "GHSA-gp8f-8m3g-qvj9",
                    "summary": "Next.js Cache Poisoning"
                },
                "info": [
                    "https://github.com/advisories/GHSA-gp8f-8m3g-qvj9",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/commit/7ed7f125e07ef0517a331009ed7e32691ba403d3",
                    "https://github.com/vercel/next.js/commit/bd164d53af259c05f1ab434004bcfdd3837d7cda",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-gp8f-8m3g-qvj9",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-46982"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "13.0.0",
                "below": "13.5.8",
                "cwe": [
                    "CWE-770"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-56332"
                    ],
                    "githubID": "GHSA-7m27-7ghc-44w9",
                    "summary": "Next.js Allows a Denial of Service (DoS) with Server Actions"
                },
                "info": [
                    "https://github.com/advisories/GHSA-7m27-7ghc-44w9",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-7m27-7ghc-44w9",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-56332"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "13.0.0",
                "below": "13.5.9",
                "cwe": [
                    "CWE-285"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-29927"
                    ],
                    "githubID": "GHSA-f82v-jwr5-mffw",
                    "summary": "Authorization Bypass in Next.js Middleware"
                },
                "info": [
                    "http://www.openwall.com/lists/oss-security/2025/03/23/3",
                    "http://www.openwall.com/lists/oss-security/2025/03/23/4",
                    "https://github.com/advisories/GHSA-f82v-jwr5-mffw",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/commit/52a078da3884efe6501613c7834a3d02a91676d2",
                    "https://github.com/vercel/next.js/commit/5fd3ae8f8542677c6294f32d18022731eab6fe48",
                    "https://github.com/vercel/next.js/releases/tag/v12.3.5",
                    "https://github.com/vercel/next.js/releases/tag/v13.5.9",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-f82v-jwr5-mffw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-29927",
                    "https://security.netapp.com/advisory/ntap-20250328-0002",
                    "https://vercel.com/changelog/vercel-firewall-proactively-protects-against-vulnerability-with-middleware"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "13.5.9",
                "below": "13.5.10",
                "cwe": [
                    "CWE-200"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-30218"
                    ],
                    "githubID": "GHSA-223j-4rm8-mrmf",
                    "summary": "Next.js may leak x-middleware-subrequest-id to external hosts"
                },
                "info": [
                    "https://github.com/advisories/GHSA-223j-4rm8-mrmf",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-223j-4rm8-mrmf",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-30218",
                    "https://vercel.com/changelog/cve-2025-30218-5DREmEH765PoeAsrNNQj3O"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "13.4.0",
                "below": "14.1.1",
                "cwe": [
                    "CWE-918"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-34351"
                    ],
                    "githubID": "GHSA-fr5h-rqp8-mj6g",
                    "summary": "Next.js Server-Side Request Forgery in Server Actions"
                },
                "info": [
                    "https://github.com/advisories/GHSA-fr5h-rqp8-mj6g",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/commit/8f7a6ca7d21a97bc9f7a1bbe10427b5ad74b9085",
                    "https://github.com/vercel/next.js/pull/62561",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-fr5h-rqp8-mj6g",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-34351"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "10.0.0",
                "below": "14.2.7",
                "cwe": [
                    "CWE-674"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-47831"
                    ],
                    "githubID": "GHSA-g77x-44xx-532m",
                    "summary": "Denial of Service condition in Next.js image optimization"
                },
                "info": [
                    "https://github.com/advisories/GHSA-g77x-44xx-532m",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/commit/d11cbc9ff0b1aaefabcba9afe1e562e0b1fde65a",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-g77x-44xx-532m",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-47831"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "14.0.0",
                "below": "14.2.10",
                "cwe": [
                    "CWE-349",
                    "CWE-639"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-46982"
                    ],
                    "githubID": "GHSA-gp8f-8m3g-qvj9",
                    "summary": "Next.js Cache Poisoning"
                },
                "info": [
                    "https://github.com/advisories/GHSA-gp8f-8m3g-qvj9",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/commit/7ed7f125e07ef0517a331009ed7e32691ba403d3",
                    "https://github.com/vercel/next.js/commit/bd164d53af259c05f1ab434004bcfdd3837d7cda",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-gp8f-8m3g-qvj9",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-46982"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "9.5.5",
                "below": "14.2.15",
                "cwe": [
                    "CWE-285"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-51479"
                    ],
                    "githubID": "GHSA-7gfc-8cq8-jh5f",
                    "summary": "Next.js authorization bypass vulnerability"
                },
                "info": [
                    "https://github.com/advisories/GHSA-7gfc-8cq8-jh5f",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/commit/1c8234eb20bc8afd396b89999a00f06b61d72d7b",
                    "https://github.com/vercel/next.js/releases/tag/v14.2.15",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-7gfc-8cq8-jh5f",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-51479"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "14.0.0",
                "below": "14.2.21",
                "cwe": [
                    "CWE-770"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-56332"
                    ],
                    "githubID": "GHSA-7m27-7ghc-44w9",
                    "summary": "Next.js Allows a Denial of Service (DoS) with Server Actions"
                },
                "info": [
                    "https://github.com/advisories/GHSA-7m27-7ghc-44w9",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-7m27-7ghc-44w9",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-56332"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "14.2.24",
                "cwe": [
                    "CWE-362"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-32421"
                    ],
                    "githubID": "GHSA-qpjv-v59x-3qc4",
                    "summary": "Next.js Race Condition to Cache Poisoning"
                },
                "info": [
                    "https://github.com/advisories/GHSA-qpjv-v59x-3qc4",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-qpjv-v59x-3qc4",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-32421",
                    "https://vercel.com/changelog/cve-2025-32421"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "14.0.0",
                "below": "14.2.25",
                "cwe": [
                    "CWE-285"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-29927"
                    ],
                    "githubID": "GHSA-f82v-jwr5-mffw",
                    "summary": "Authorization Bypass in Next.js Middleware"
                },
                "info": [
                    "http://www.openwall.com/lists/oss-security/2025/03/23/3",
                    "http://www.openwall.com/lists/oss-security/2025/03/23/4",
                    "https://github.com/advisories/GHSA-f82v-jwr5-mffw",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/commit/52a078da3884efe6501613c7834a3d02a91676d2",
                    "https://github.com/vercel/next.js/commit/5fd3ae8f8542677c6294f32d18022731eab6fe48",
                    "https://github.com/vercel/next.js/releases/tag/v12.3.5",
                    "https://github.com/vercel/next.js/releases/tag/v13.5.9",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-f82v-jwr5-mffw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-29927",
                    "https://security.netapp.com/advisory/ntap-20250328-0002",
                    "https://vercel.com/changelog/vercel-firewall-proactively-protects-against-vulnerability-with-middleware"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "14.2.25",
                "below": "14.2.26",
                "cwe": [
                    "CWE-200"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-30218"
                    ],
                    "githubID": "GHSA-223j-4rm8-mrmf",
                    "summary": "Next.js may leak x-middleware-subrequest-id to external hosts"
                },
                "info": [
                    "https://github.com/advisories/GHSA-223j-4rm8-mrmf",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-223j-4rm8-mrmf",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-30218",
                    "https://vercel.com/changelog/cve-2025-30218-5DREmEH765PoeAsrNNQj3O"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "15.0.0",
                "below": "15.1.2",
                "cwe": [
                    "CWE-770"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-56332"
                    ],
                    "githubID": "GHSA-7m27-7ghc-44w9",
                    "summary": "Next.js Allows a Denial of Service (DoS) with Server Actions"
                },
                "info": [
                    "https://github.com/advisories/GHSA-7m27-7ghc-44w9",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-7m27-7ghc-44w9",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-56332"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "15.0.0",
                "below": "15.1.6",
                "cwe": [
                    "CWE-362"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-32421"
                    ],
                    "githubID": "GHSA-qpjv-v59x-3qc4",
                    "summary": "Next.js Race Condition to Cache Poisoning"
                },
                "info": [
                    "https://github.com/advisories/GHSA-qpjv-v59x-3qc4",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-qpjv-v59x-3qc4",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-32421",
                    "https://vercel.com/changelog/cve-2025-32421"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "13.0",
                "below": "15.2.2",
                "cwe": [
                    "CWE-1385"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-48068"
                    ],
                    "githubID": "GHSA-3h52-269p-cp9r",
                    "summary": "Information exposure in Next.js dev server due to lack of origin verification"
                },
                "info": [
                    "https://github.com/advisories/GHSA-3h52-269p-cp9r",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-3h52-269p-cp9r",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-48068",
                    "https://vercel.com/changelog/cve-2025-48068"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "15.0.0",
                "below": "15.2.3",
                "cwe": [
                    "CWE-285"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-29927"
                    ],
                    "githubID": "GHSA-f82v-jwr5-mffw",
                    "summary": "Authorization Bypass in Next.js Middleware"
                },
                "info": [
                    "http://www.openwall.com/lists/oss-security/2025/03/23/3",
                    "http://www.openwall.com/lists/oss-security/2025/03/23/4",
                    "https://github.com/advisories/GHSA-f82v-jwr5-mffw",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/commit/52a078da3884efe6501613c7834a3d02a91676d2",
                    "https://github.com/vercel/next.js/commit/5fd3ae8f8542677c6294f32d18022731eab6fe48",
                    "https://github.com/vercel/next.js/releases/tag/v12.3.5",
                    "https://github.com/vercel/next.js/releases/tag/v13.5.9",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-f82v-jwr5-mffw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-29927",
                    "https://security.netapp.com/advisory/ntap-20250328-0002",
                    "https://vercel.com/changelog/vercel-firewall-proactively-protects-against-vulnerability-with-middleware"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "15.2.3",
                "below": "15.2.4",
                "cwe": [
                    "CWE-200"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2025-30218"
                    ],
                    "githubID": "GHSA-223j-4rm8-mrmf",
                    "summary": "Next.js may leak x-middleware-subrequest-id to external hosts"
                },
                "info": [
                    "https://github.com/advisories/GHSA-223j-4rm8-mrmf",
                    "https://github.com/vercel/next.js",
                    "https://github.com/vercel/next.js/security/advisories/GHSA-223j-4rm8-mrmf",
                    "https://nvd.nist.gov/vuln/detail/CVE-2025-30218",
                    "https://vercel.com/changelog/cve-2025-30218-5DREmEH765PoeAsrNNQj3O"
                ],
                "severity": "low"
            }
        ]
    },
    "pdf.js": {
        "bowername": [
            "pdfjs-dist"
        ],
        "extractors": {
            "filecontent": [
                "(?:const|var) pdfjsVersion = ['\"]([0-9][0-9.a-z_-]+)['\"];",
                "PDFJS.version ?= ?['\"]([0-9][0-9.a-z_-]+)['\"]",
                "apiVersion: ?['\"]([0-9][0-9.a-z_-]+)['\"][\\s\\S]*,data(:[a-zA-Z.]{1,6})?,[\\s\\S]*password(:[a-zA-Z.]{1,10})?,[\\s\\S]*disableAutoFetch(:[a-zA-Z.]{1,22})?,[\\s\\S]*rangeChunkSize",
                "messageHandler\\.sendWithPromise\\(\"GetDocRequest\",\\{docId:[a-zA-Z],apiVersion:\"([0-9][0-9.a-z_-]+)\""
            ],
            "uri": [
                "/pdf\\.js/([0-9][0-9.a-z_-]+)/",
                "/pdfjs-dist@([0-9][0-9.a-z_-]+)/"
            ]
        },
        "npmname": "pdfjs-dist",
        "vulnerabilities": [
            {
                "atOrAbove": "0",
                "below": "1.10.100",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-5158"
                    ],
                    "githubID": "GHSA-7jg2-jgv3-fmr4",
                    "summary": "Malicious PDF can inject JavaScript into PDF Viewer"
                },
                "info": [
                    "http://www.securityfocus.com/bid/104136",
                    "http://www.securitytracker.com/id/1040896",
                    "https://access.redhat.com/errata/RHSA-2018:1414",
                    "https://access.redhat.com/errata/RHSA-2018:1415",
                    "https://bugzilla.mozilla.org/show_bug.cgi?id=1452075",
                    "https://github.com/advisories/GHSA-7jg2-jgv3-fmr4",
                    "https://github.com/mozilla/pdf.js",
                    "https://github.com/mozilla/pdf.js/commit/2dc4af525d1612c98afcd1e6bee57d4788f78f97",
                    "https://github.com/mozilla/pdf.js/pull/9659",
                    "https://lists.debian.org/debian-lts-announce/2018/05/msg00007.html",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-5158",
                    "https://security.gentoo.org/glsa/201810-01",
                    "https://usn.ubuntu.com/3645-1",
                    "https://www.debian.org/security/2018/dsa-4199",
                    "https://www.mozilla.org/security/advisories/mfsa2018-11",
                    "https://www.mozilla.org/security/advisories/mfsa2018-12"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "2.0.0",
                "below": "2.0.550",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-5158"
                    ],
                    "githubID": "GHSA-7jg2-jgv3-fmr4",
                    "summary": "Malicious PDF can inject JavaScript into PDF Viewer"
                },
                "info": [
                    "http://www.securityfocus.com/bid/104136",
                    "http://www.securitytracker.com/id/1040896",
                    "https://access.redhat.com/errata/RHSA-2018:1414",
                    "https://access.redhat.com/errata/RHSA-2018:1415",
                    "https://bugzilla.mozilla.org/show_bug.cgi?id=1452075",
                    "https://github.com/advisories/GHSA-7jg2-jgv3-fmr4",
                    "https://github.com/mozilla/pdf.js",
                    "https://github.com/mozilla/pdf.js/commit/2dc4af525d1612c98afcd1e6bee57d4788f78f97",
                    "https://github.com/mozilla/pdf.js/pull/9659",
                    "https://lists.debian.org/debian-lts-announce/2018/05/msg00007.html",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-5158",
                    "https://security.gentoo.org/glsa/201810-01",
                    "https://usn.ubuntu.com/3645-1",
                    "https://www.debian.org/security/2018/dsa-4199",
                    "https://www.mozilla.org/security/advisories/mfsa2018-11",
                    "https://www.mozilla.org/security/advisories/mfsa2018-12"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0",
                "below": "4.2.67",
                "cwe": [
                    "CWE-754"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-4367"
                    ],
                    "githubID": "GHSA-wgrm-67xf-hhpq",
                    "summary": "PDF.js vulnerable to arbitrary JavaScript execution upon opening a malicious PDF"
                },
                "info": [
                    "https://bugzilla.mozilla.org/show_bug.cgi?id=1893645",
                    "https://github.com/advisories/GHSA-wgrm-67xf-hhpq",
                    "https://github.com/mozilla/pdf.js",
                    "https://github.com/mozilla/pdf.js/commit/85e64b5c16c9aaef738f421733c12911a441cec6",
                    "https://github.com/mozilla/pdf.js/pull/18015",
                    "https://github.com/mozilla/pdf.js/security/advisories/GHSA-wgrm-67xf-hhpq"
                ],
                "severity": "high"
            }
        ]
    },
    "pdfobject": {
        "extractors": {
            "filecontent": [
                "/*[\\s]+PDFObject v([0-9][0-9.a-z_-]+)",
                "\\* +PDFObject v([0-9][0-9.a-z_-]+)",
                "let pdfobjectversion = \"([0-9][0-9.a-z_-]+)\";",
                "pdfobjectversion:\"([0-9][0-9.a-z_-]+)\""
            ],
            "uri": [
                "/pdfobject/([0-9][0-9.a-z_-]+)/pdfobject(\\.min)?\\.js",
                "/pdfobject@([0-9][0-9.a-z_-]+)/"
            ]
        },
        "vulnerabilities": []
    },
    "pendo": {
        "extractors": {
            "filecontent": [
                "// Pendo Agent Wrapper\n//[\\s]+Environment:[\\s]+[^\n]+\n// Agent Version:[\\s]+([0-9][0-9.a-z_-]+)"
            ],
            "func": [
                "pendo.VERSION.split('_')[0]"
            ]
        },
        "vulnerabilities": [
            {
                "below": "2.15.18",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "74",
                    "summary": "Patched XSS vulnerability around script loading"
                },
                "info": [
                    "https://developers.pendo.io/agent-version-2-15-18/"
                ],
                "severity": "medium"
            }
        ]
    },
    "plupload": {
        "bowername": [
            "Plupload",
            "plupload"
        ],
        "extractors": {
            "filecontent": [
                "\\* Plupload - multi-runtime File Uploader(?:\r|\n)+ \\* v([0-9][0-9.a-z_-]+)",
                "var g=\\{VERSION:\"([0-9][0-9.a-z_-]+)\",.*;window.plupload=g\\}"
            ],
            "filename": [
                "plupload-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "plupload.VERSION"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/plupload(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "1.5.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2012-2401"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2012-2401/"
                ],
                "severity": "medium"
            },
            {
                "below": "1.5.5",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-0237"
                    ]
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2013-0237/"
                ],
                "severity": "medium"
            },
            {
                "below": "2.1.9",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2016-4566"
                    ]
                },
                "info": [
                    "https://github.com/moxiecode/plupload/releases"
                ],
                "severity": "medium"
            },
            {
                "below": "2.3.7",
                "cwe": [
                    "CWE-434"
                ],
                "identifiers": {
                    "retid": "35",
                    "summary": "Fixed security vulnerability by adding die calls to all php files to prevent them from being executed unless modified."
                },
                "info": [
                    "https://github.com/moxiecode/plupload/releases/tag/v2.3.7"
                ],
                "severity": "medium"
            },
            {
                "below": "2.3.8",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "38",
                    "summary": "Fixed a potential security issue with not entity encoding the file names in the html in the queue/ui widgets."
                },
                "info": [
                    "https://github.com/moxiecode/plupload/releases/tag/v2.3.8"
                ],
                "severity": "medium"
            },
            {
                "below": "2.3.9",
                "cwe": [
                    "CWE-434",
                    "CWE-75"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-23562"
                    ],
                    "githubID": "GHSA-rp2c-jrgp-cvr8",
                    "retid": "42",
                    "summary": "Fixed another case of html entities not being encoded that could be exploded by uploading a file name with html in it."
                },
                "info": [
                    "https://github.com/moxiecode/plupload/releases/tag/v2.3.9"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.0.0",
                "below": "3.1.3",
                "cwe": [
                    "CWE-434"
                ],
                "identifiers": {
                    "retid": "36",
                    "summary": "Fixed security vulnerability by adding die calls to all php files to prevent them from being executed unless modified."
                },
                "info": [
                    "https://github.com/moxiecode/plupload/releases/tag/v3.1.3"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.0.0",
                "below": "3.1.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "37",
                    "summary": "Fixed a potential security issue with not entity encoding the file names in the html in the queue/ui widgets."
                },
                "info": [
                    "https://github.com/moxiecode/plupload/releases/tag/v3.1.4"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "3.0.0",
                "below": "3.1.5",
                "cwe": [
                    "CWE-434"
                ],
                "identifiers": {
                    "retid": "41",
                    "summary": "Fixed another case of html entities not being encoded that could be exploded by uploading a file name with html in it."
                },
                "info": [
                    "https://github.com/moxiecode/plupload/releases/tag/v3.1.5"
                ],
                "severity": "medium"
            }
        ]
    },
    "prototypejs": {
        "bowername": [
            "prototype.js",
            "prototypejs",
            "prototypejs-bower"
        ],
        "extractors": {
            "filecontent": [
                "Prototype JavaScript framework, version ([0-9][0-9.a-z_-]+)",
                "Prototype[ ]?=[ ]?\\{[ \r\n\t]*Version:[ ]?(?:'|\")([0-9][0-9.a-z_-]+)(?:'|\")"
            ],
            "filename": [
                "prototype-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "Prototype.Version"
            ],
            "hashes": {},
            "uri": [
                "/([0-9][0-9.a-z_-]+)/prototype(\\.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "1.5.1.2",
                "cwe": [
                    "CWE-942"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2008-7220"
                    ]
                },
                "info": [
                    "http://prototypejs.org/2008/01/25/prototype-1-6-0-2-bug-fixes-performance-improvements-and-security/",
                    "http://www.cvedetails.com/cve/CVE-2008-7220/"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.6.0",
                "below": "1.6.0.2",
                "cwe": [
                    "CWE-942"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2008-7220"
                    ]
                },
                "info": [
                    "http://prototypejs.org/2008/01/25/prototype-1-6-0-2-bug-fixes-performance-improvements-and-security/",
                    "http://www.cvedetails.com/cve/CVE-2008-7220/"
                ],
                "severity": "high"
            }
        ]
    },
    "react": {
        "extractors": {
            "filecontent": [
                "\"\\./ReactReconciler\":[0-9]+,\"\\./Transaction\":[0-9]+,\"fbjs/lib/invariant\":[0-9]+\\}\\],[0-9]+:\\[function\\(require,module,exports\\)\\{\"use strict\";module\\.exports=\"([0-9][0-9.a-z_-]+)\"\\}",
                "/\\*\\*\n +\\* React \\(with addons\\) ?v([0-9][0-9.a-z_-]+)",
                "/\\*\\*\n +\\* React v([0-9][0-9.a-z_-]+)",
                "/\\*\\* @license React v([0-9][0-9.a-z_-]+)[\\s]*\\* react(-jsx-runtime)?\\.",
                "ReactVersion\\.js[\\*! \\\\/\n\r]{0,100}function\\(e,t\\)\\{\"use strict\";e\\.exports=\"([0-9][0-9.a-z_-]+)\"",
                "expected a ReactNode.[\\s\\S]{0,1800}?function\\(e,t\\)\\{\"use strict\";e\\.exports=\"([0-9][0-9.a-z_-]+)\""
            ],
            "func": [
                "react.version",
                "require('react').version"
            ]
        },
        "vulnerabilities": [
            {
                "atOrAbove": "0.4.0",
                "below": "0.4.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-7035"
                    ],
                    "githubID": "GHSA-g53w-52xc-2j85",
                    "summary": "potential XSS vulnerability can arise when using user data as a key"
                },
                "info": [
                    "https://facebook.github.io/react/blog/2013/12/18/react-v0.5.2-v0.4.2.html",
                    "https://github.com/advisories/GHSA-g53w-52xc-2j85"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0.5.0",
                "below": "0.5.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2013-7035"
                    ],
                    "githubID": "GHSA-g53w-52xc-2j85",
                    "summary": "potential XSS vulnerability can arise when using user data as a key"
                },
                "info": [
                    "https://facebook.github.io/react/blog/2013/12/18/react-v0.5.2-v0.4.2.html",
                    "https://github.com/advisories/GHSA-g53w-52xc-2j85"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0.0.1",
                "below": "0.14.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-hg79-j56m-fxgv",
                    "retid": "23",
                    "summary": " including untrusted objects as React children can result in an XSS security vulnerability"
                },
                "info": [
                    "http://danlec.com/blog/xss-via-a-spoofed-react-element",
                    "https://facebook.github.io/react/blog/2015/10/07/react-v0.14.html"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "16.0.0",
                "below": "16.0.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6341"
                    ],
                    "summary": "potential XSS vulnerability when the attacker controls an attribute name"
                },
                "info": [
                    "https://github.com/facebook/react/blob/master/CHANGELOG.md",
                    "https://reactjs.org/blog/2018/08/01/react-v-16-4-2.html"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "16.1.0",
                "below": "16.1.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6341"
                    ],
                    "summary": "potential XSS vulnerability when the attacker controls an attribute name"
                },
                "info": [
                    "https://github.com/facebook/react/blob/master/CHANGELOG.md",
                    "https://reactjs.org/blog/2018/08/01/react-v-16-4-2.html"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "16.2.0",
                "below": "16.2.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6341"
                    ],
                    "summary": "potential XSS vulnerability when the attacker controls an attribute name"
                },
                "info": [
                    "https://github.com/facebook/react/blob/master/CHANGELOG.md",
                    "https://reactjs.org/blog/2018/08/01/react-v-16-4-2.html"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "16.3.0",
                "below": "16.3.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6341"
                    ],
                    "summary": "potential XSS vulnerability when the attacker controls an attribute name"
                },
                "info": [
                    "https://github.com/facebook/react/blob/master/CHANGELOG.md",
                    "https://reactjs.org/blog/2018/08/01/react-v-16-4-2.html"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "16.4.0",
                "below": "16.4.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6341"
                    ],
                    "summary": "potential XSS vulnerability when the attacker controls an attribute name"
                },
                "info": [
                    "https://github.com/facebook/react/blob/master/CHANGELOG.md",
                    "https://reactjs.org/blog/2018/08/01/react-v-16-4-2.html"
                ],
                "severity": "medium"
            }
        ]
    },
    "react-dom": {
        "extractors": {
            "filecontent": [
                "/\\*\\* @license React v([0-9][0-9.a-z_-]+)[\\s]*\\* react-dom\\.",
                "version:\"([0-9][0-9.a-z_-]+)[a-z0-9\\-]*\"[\\s,]*rendererPackageName:\"react-dom\""
            ],
            "uri": [
                "/react-dom@([0-9][0-9.a-z_-]+)/"
            ]
        },
        "vulnerabilities": [
            {
                "atOrAbove": "16.0.0",
                "below": "16.0.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6341"
                    ],
                    "githubID": "GHSA-mvjj-gqq2-p4hw",
                    "summary": "Affected versions of `react-dom` are vulnerable to Cross-Site Scripting (XSS). The package fails to validate attribute names in HTML tags which may lead to Cross-Site Scripting in specific scenarios"
                },
                "info": [
                    "https://github.com/advisories/GHSA-mvjj-gqq2-p4hw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-6341",
                    "https://reactjs.org/blog/2018/08/01/react-v-16-4-2.html"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "16.1.0",
                "below": "16.1.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6341"
                    ],
                    "githubID": "GHSA-mvjj-gqq2-p4hw",
                    "summary": "Affected versions of `react-dom` are vulnerable to Cross-Site Scripting (XSS). The package fails to validate attribute names in HTML tags which may lead to Cross-Site Scripting in specific scenarios"
                },
                "info": [
                    "https://github.com/advisories/GHSA-mvjj-gqq2-p4hw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-6341",
                    "https://reactjs.org/blog/2018/08/01/react-v-16-4-2.html"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "16.2.0",
                "below": "16.2.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6341"
                    ],
                    "githubID": "GHSA-mvjj-gqq2-p4hw",
                    "summary": "Affected versions of `react-dom` are vulnerable to Cross-Site Scripting (XSS). The package fails to validate attribute names in HTML tags which may lead to Cross-Site Scripting in specific scenarios"
                },
                "info": [
                    "https://github.com/advisories/GHSA-mvjj-gqq2-p4hw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-6341",
                    "https://reactjs.org/blog/2018/08/01/react-v-16-4-2.html"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "16.3.0",
                "below": "16.3.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6341"
                    ],
                    "githubID": "GHSA-mvjj-gqq2-p4hw",
                    "summary": "Affected versions of `react-dom` are vulnerable to Cross-Site Scripting (XSS). The package fails to validate attribute names in HTML tags which may lead to Cross-Site Scripting in specific scenarios"
                },
                "info": [
                    "https://github.com/advisories/GHSA-mvjj-gqq2-p4hw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-6341",
                    "https://reactjs.org/blog/2018/08/01/react-v-16-4-2.html"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "16.4.0",
                "below": "16.4.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2018-6341"
                    ],
                    "githubID": "GHSA-mvjj-gqq2-p4hw",
                    "summary": "Affected versions of `react-dom` are vulnerable to Cross-Site Scripting (XSS). The package fails to validate attribute names in HTML tags which may lead to Cross-Site Scripting in specific scenarios"
                },
                "info": [
                    "https://github.com/advisories/GHSA-mvjj-gqq2-p4hw",
                    "https://nvd.nist.gov/vuln/detail/CVE-2018-6341",
                    "https://reactjs.org/blog/2018/08/01/react-v-16-4-2.html"
                ],
                "severity": "medium"
            }
        ]
    },
    "react-is": {
        "extractors": {
            "filecontent": [
                "/\\*\\* @license React v([0-9][0-9.a-z_-]+)[\\s]*\\* react-is\\."
            ]
        },
        "vulnerabilities": []
    },
    "retire-example": {
        "extractors": {
            "filecontent": [
                "/\\*!? Retire-example v([0-9][0-9.a-z_-]+)"
            ],
            "filename": [
                "retire-example-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "func": [
                "retire.VERSION"
            ],
            "hashes": {
                "07f8b94c8d601a24a1914a1a92bec0e4fafda964": "0.0.1"
            }
        },
        "vulnerabilities": [
            {
                "below": "0.0.2",
                "cwe": [
                    "CWE-477"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-XXXX-XXXX"
                    ],
                    "bug": "1234",
                    "summary": "bug summary"
                },
                "info": [
                    "http://github.com/eoftedal/retire.js/"
                ],
                "severity": "low"
            }
        ]
    },
    "scheduler": {
        "extractors": {
            "filecontent": [
                "/\\*\\* @license React v([0-9][0-9.a-z_-]+)[\\s]*\\* scheduler\\."
            ]
        },
        "vulnerabilities": []
    },
    "select2": {
        "extractors": {
            "filecontent": [
                "/\\*!(?:[\\s]+\\*)? Select2 ([0-9][0-9.a-z_-]+)",
                "/\\*[\\s]+Copyright 20[0-9]{2} [I]gor V[a]ynberg[\\s]+Version: ([0-9][0-9.a-z_-]+)[\\s\\S]{1,5000}(\\.attr\\(\"class\",\"select2-sizer\"|\\.data\\(document, *\"select2-lastpos\"|document\\)\\.data\\(\"select2-lastpos\"|SingleSelect2, *MultiSelect2|window.Select2 *!== *undefined)"
            ],
            "uri": [
                "([0-9][0-9.a-z_-]+)/(js/)?select2(.min)?\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "atOrAbove": "0",
                "below": "4.0.6",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2016-10744"
                    ],
                    "githubID": "GHSA-rf66-hmqf-q3fc",
                    "summary": "Improper Neutralization of Input During Web Page Generation in Select2"
                },
                "info": [
                    "https://github.com/advisories/GHSA-rf66-hmqf-q3fc",
                    "https://github.com/select2/select2",
                    "https://github.com/select2/select2/issues/4587",
                    "https://github.com/snipe/snipe-it/pull/6831",
                    "https://github.com/snipe/snipe-it/pull/6831/commits/5848d9a10c7d62c73ff6a3858edfae96a429402a",
                    "https://nvd.nist.gov/vuln/detail/CVE-2016-10744"
                ],
                "severity": "medium"
            }
        ]
    },
    "sessvars": {
        "extractors": {
            "filecontent": [
                "sessvars ver ([0-9][0-9.a-z_-]+)"
            ],
            "filename": [
                "sessvars-([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "hashes": {}
        },
        "vulnerabilities": [
            {
                "below": "1.01",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "summary": "Unsanitized data passed to eval()",
                    "tenable": "98645"
                },
                "info": [
                    "http://www.thomasfrank.se/sessionvars.html"
                ],
                "severity": "low"
            }
        ]
    },
    "svelte": {
        "extractors": {
            "filecontent": [
                "VERSION = '([0-9][0-9.a-z_-]+)'[\\s\\S]{21,200}parse\\$[0-9][\\s\\S]{10,80}preprocess",
                "generated by Svelte v([0-9][0-9.a-z_-]+) \\*/",
                "generated by Svelte v\\$\\{['\"]([0-9][0-9.a-z_-]+)['\"]\\}",
                "var version\\$[0-9] = \"([0-9][0-9.a-z_-]+)\";[\\s\\S]{10,30}normalizeOptions\\(options\\)[\\s\\S]{80,200}'SvelteComponent.html'",
                "version: '([0-9][0-9.a-z_-]+)' [\\s\\S]{80,200}'SvelteDOMInsert'"
            ],
            "filename": [
                "svelte[@\\-]([0-9][0-9.a-z_-]+)(.min)?\\.m?js"
            ],
            "func": [
                "svelte.VERSION"
            ],
            "uri": [
                "/svelte@([0-9][0-9.a-z_-]+)/"
            ]
        },
        "vulnerabilities": [
            {
                "below": "2.9.8",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "9",
                    "summary": "XSS"
                },
                "info": [
                    "https://github.com/sveltejs/svelte/pull/1623"
                ],
                "severity": "medium"
            },
            {
                "below": "3.46.5",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "8",
                    "summary": "XSS"
                },
                "info": [
                    "https://github.com/sveltejs/svelte/pull/7333"
                ],
                "severity": "medium"
            },
            {
                "below": "3.49.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-25875"
                    ],
                    "githubID": "GHSA-wv8q-r932-8hc7",
                    "issue": "7530",
                    "summary": "XSS"
                },
                "info": [
                    "https://github.com/sveltejs/svelte/pull/7530"
                ],
                "severity": "medium"
            },
            {
                "below": "4.2.19",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-45047"
                    ],
                    "githubID": "GHSA-8266-84wp-wv5c",
                    "summary": "Svelte has a potential mXSS vulnerability due to improper HTML escaping"
                },
                "info": [
                    "https://github.com/advisories/GHSA-8266-84wp-wv5c",
                    "https://github.com/sveltejs/svelte",
                    "https://github.com/sveltejs/svelte/commit/83e96e044deb5ecbae2af361ae9e31d3e1ac43a3",
                    "https://github.com/sveltejs/svelte/security/advisories/GHSA-8266-84wp-wv5c",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-45047"
                ],
                "severity": "medium"
            }
        ]
    },
    "swfobject": {
        "bowername": [
            "swfobject",
            "swfobject-bower"
        ],
        "extractors": {
            "filecontent": [
                "SWFObject v([0-9][0-9.a-z_-]+) "
            ],
            "filename": [
                "swfobject_([0-9][0-9.a-z_-]+)(.min)?\\.js"
            ],
            "hashes": {}
        },
        "vulnerabilities": [
            {
                "below": "2.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "1",
                    "summary": "DOM-based XSS"
                },
                "info": [
                    "https://github.com/swfobject/swfobject/wiki/SWFObject-Release-Notes#swfobject-v21-beta7-june-6th-2008"
                ],
                "severity": "medium"
            }
        ]
    },
    "tableexport.jquery.plugin": {
        "extractors": {
            "filecontent": [
                "/\\*![\\s]+\\* TableExport.js v([0-9][0-9.a-z_-]+)",
                "/\\*[\\s]+tableExport.jquery.plugin[\\s]+Version ([0-9][0-9.a-z_-]+)"
            ],
            "uri": [
                "/TableExport/([0-9][0-9.a-z_-]+)/js/tableexport.min.js",
                "/tableexport.jquery.plugin@([0-9][0-9.a-z_-]+)/tableExport.min.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "1.25.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-1291"
                    ],
                    "githubID": "GHSA-j636-crp3-m584",
                    "summary": "There is a cross-site scripting vulnerability with default `onCellHtmlData`"
                },
                "info": [
                    "https://github.com/hhurz/tableexport.jquery.plugin/commit/dcbaee23cf98328397a153e71556f75202988ec9"
                ],
                "severity": "medium"
            }
        ]
    },
    "tinyMCE": {
        "bowername": [
            "tinymce",
            "tinymce-dist"
        ],
        "extractors": {
            "filecontent": [
                "// ([0-9][0-9.a-z_-]+) \\([0-9\\-]+\\)[\n\r]+.{0,1200}l=.tinymce/geom/Rect.",
                "/\\*\\*[\\s]*\\* TinyMCE version ([0-9][0-9.a-z_-]+)"
            ],
            "filecontentreplace": [
                "/majorVersion:.([0-9]+).,minorVersion:.([0-9.]+).,.*tinyMCEPreInit/$1.$2/",
                "/tinyMCEPreInit.*majorVersion:.([0-9]+).,minorVersion:.([0-9.]+)./$1.$2/"
            ],
            "func": [
                "tinyMCE.majorVersion + '.'+ tinyMCE.minorVersion"
            ],
            "uri": [
                "/tinymce/([0-9][0-9.a-z_-]+)/tinymce(\\.min)?\\.js"
            ]
        },
        "npmname": "tinymce",
        "vulnerabilities": [
            {
                "below": "1.4.2",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2011-4825"
                    ],
                    "summary": "Static code injection vulnerability in inc/function.base.php"
                },
                "info": [
                    "http://www.cvedetails.com/cve/CVE-2011-4825/"
                ],
                "severity": "high"
            },
            {
                "below": "4.2.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "62",
                    "summary": "FIXED so script elements gets removed by default to prevent possible XSS issues in default config implementations"
                },
                "info": [
                    "https://www.tinymce.com/docs/changelog/"
                ],
                "severity": "medium"
            },
            {
                "below": "4.2.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "61",
                    "summary": "xss issues with media plugin not properly filtering out some script attributes."
                },
                "info": [
                    "https://www.tinymce.com/docs/changelog/"
                ],
                "severity": "medium"
            },
            {
                "below": "4.7.12",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "63",
                    "summary": "FIXED so links with xlink:href attributes are filtered correctly to prevent XSS."
                },
                "info": [
                    "https://www.tinymce.com/docs/changelog/"
                ],
                "severity": "medium"
            },
            {
                "below": "4.9.7",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-17480"
                    ],
                    "githubID": "GHSA-27gm-ghr9-4v95",
                    "summary": "The vulnerability allowed arbitrary JavaScript execution when inserting a specially crafted piece of content into the editor via the clipboard or APIs"
                },
                "info": [
                    "https://github.com/advisories/GHSA-27gm-ghr9-4v95",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-27gm-ghr9-4v95"
                ],
                "severity": "high"
            },
            {
                "below": "4.9.7",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-p7j5-4mwm-hv86",
                    "summary": "TinyMCE before 4.9.7 and 5.x before 5.1.4 allows XSS in the core parser, the paste plugin, and the visualchars plugin by using the clipboard or APIs to insert content into the editor."
                },
                "info": [
                    "https://github.com/advisories/GHSA-p7j5-4mwm-hv86",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-p7j5-4mwm-hv86"
                ],
                "severity": "high"
            },
            {
                "below": "4.9.10",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-1010091"
                    ],
                    "githubID": "GHSA-c78w-2gw7-gjv3",
                    "summary": "cross-site scripting (XSS) vulnerability was discovered in: the core parser and `media` plugin. "
                },
                "info": [
                    "https://github.com/advisories/GHSA-c78w-2gw7-gjv3",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-vrv8-v4w8-f95h"
                ],
                "severity": "medium"
            },
            {
                "below": "4.9.11",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-12648"
                    ],
                    "githubID": "GHSA-vrv8-v4w8-f95h",
                    "summary": "Cross-site scripting vulnerability in TinyMCE"
                },
                "info": [
                    "https://github.com/advisories/GHSA-vrv8-v4w8-f95h",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-vrv8-v4w8-f95h"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "5.0.0",
                "below": "5.1.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-17480"
                    ],
                    "githubID": "GHSA-27gm-ghr9-4v95",
                    "summary": "The vulnerability allowed arbitrary JavaScript execution when inserting a specially crafted piece of content into the editor via the clipboard or APIs"
                },
                "info": [
                    "https://github.com/advisories/GHSA-27gm-ghr9-4v95",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-27gm-ghr9-4v95"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "5.0.0",
                "below": "5.1.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-p7j5-4mwm-hv86",
                    "summary": "TinyMCE before 4.9.7 and 5.x before 5.1.4 allows XSS in the core parser, the paste plugin, and the visualchars plugin by using the clipboard or APIs to insert content into the editor."
                },
                "info": [
                    "https://github.com/advisories/GHSA-p7j5-4mwm-hv86",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-p7j5-4mwm-hv86"
                ],
                "severity": "high"
            },
            {
                "below": "5.1.6",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "64",
                    "summary": "CDATA parsing and sanitization has been improved to address a cross-site scripting (XSS) vulnerability."
                },
                "info": [
                    "https://www.tiny.cloud/docs/release-notes/release-notes516/"
                ],
                "severity": "medium"
            },
            {
                "below": "5.2.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "65",
                    "summary": "media embed content not processing safely in some cases."
                },
                "info": [
                    "https://www.tiny.cloud/docs/release-notes/release-notes522/"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "5.0.0",
                "below": "5.2.2",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2019-1010091"
                    ],
                    "githubID": "GHSA-c78w-2gw7-gjv3",
                    "summary": "cross-site scripting (XSS) vulnerability was discovered in: the core parser and `media` plugin. "
                },
                "info": [
                    "https://github.com/advisories/GHSA-c78w-2gw7-gjv3",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-vrv8-v4w8-f95h"
                ],
                "severity": "medium"
            },
            {
                "below": "5.4.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "66",
                    "summary": "content in an iframe element parsing as DOM elements instead of text content."
                },
                "info": [
                    "https://www.tiny.cloud/docs/release-notes/release-notes54/"
                ],
                "severity": "low"
            },
            {
                "atOrAbove": "5.0.0",
                "below": "5.4.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-12648"
                    ],
                    "githubID": "GHSA-vrv8-v4w8-f95h",
                    "summary": "Cross-site scripting vulnerability in TinyMCE"
                },
                "info": [
                    "https://github.com/advisories/GHSA-vrv8-v4w8-f95h",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-vrv8-v4w8-f95h"
                ],
                "severity": "medium"
            },
            {
                "below": "5.6.0",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "githubID": "GHSA-h96f-fc7c-9r55",
                    "summary": "Regex denial of service vulnerability in codesample plugin"
                },
                "info": [
                    "https://www.tiny.cloud/docs/release-notes/release-notes56/#securityfixes"
                ],
                "severity": "low"
            },
            {
                "below": "5.6.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-21911"
                    ],
                    "githubID": "GHSA-w7jx-j77m-wp65",
                    "retid": "67",
                    "summary": "security issue where URLs in attributes weren\u2019t correctly sanitized. security issue in the codesample plugin"
                },
                "info": [
                    "https://www.tiny.cloud/docs/release-notes/release-notes56/#securityfixes"
                ],
                "severity": "medium"
            },
            {
                "below": "5.7.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "githubID": "GHSA-5vm8-hhgr-jcjp",
                    "retid": "68",
                    "summary": "URLs are not correctly filtered in some cases."
                },
                "info": [
                    "https://www.tiny.cloud/docs/release-notes/release-notes571/#securityfixes"
                ],
                "severity": "medium"
            },
            {
                "below": "5.9.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-21908"
                    ],
                    "githubID": "GHSA-5h9g-x5rv-25wg",
                    "retid": "69",
                    "summary": "Inserting certain HTML content into the editor could result in invalid HTML once parsed. This caused a medium severity Cross Site Scripting (XSS) vulnerability"
                },
                "info": [
                    "https://www.tiny.cloud/docs/release-notes/release-notes59/#securityfixes"
                ],
                "severity": "medium"
            },
            {
                "below": "5.10.0",
                "cwe": [
                    "CWE-64",
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-21910"
                    ],
                    "githubID": "GHSA-r8hm-w5f7-wj39",
                    "retid": "70",
                    "summary": "URLs not cleaned correctly in some cases in the link and image plugins"
                },
                "info": [
                    "https://www.tiny.cloud/docs/release-notes/release-notes510/#securityfixes"
                ],
                "severity": "medium"
            },
            {
                "below": "5.10.7",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-23494"
                    ],
                    "githubID": "GHSA-gg8r-xjwq-4w92",
                    "summary": "A cross-site scripting (XSS) vulnerability in TinyMCE alerts which allowed arbitrary JavaScript execution was found and fixed."
                },
                "info": [
                    "https://github.com/advisories/GHSA-gg8r-xjwq-4w92",
                    "https://www.cve.org/CVERecord?id=CVE-2022-23494",
                    "https://www.tiny.cloud/docs/changelog/#5107-2022-12-06"
                ],
                "severity": "medium"
            },
            {
                "below": "5.10.8",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-45819"
                    ],
                    "githubID": "GHSA-hgqx-r2hp-jr38",
                    "summary": "TinyMCE XSS vulnerability in notificationManager.open API"
                },
                "info": [
                    "https://github.com/advisories/GHSA-hgqx-r2hp-jr38",
                    "https://www.cve.org/CVERecord?id=CVE-2022-23494",
                    "https://www.tiny.cloud/docs/changelog/#5107-2022-12-06"
                ],
                "severity": "medium"
            },
            {
                "below": "5.10.8",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-45818"
                    ],
                    "githubID": "GHSA-v65r-p3vv-jjfv",
                    "summary": "TinyMCE mXSS vulnerability in undo/redo, getContent API, resetContent API, and Autosave plugin"
                },
                "info": [
                    "https://github.com/advisories/GHSA-v65r-p3vv-jjfv"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "5.10.9",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-48219"
                    ],
                    "githubID": "GHSA-v626-r774-j7f8",
                    "summary": "TinyMCE vulnerable to mutation Cross-site Scripting via special characters in unescaped text nodes"
                },
                "info": [
                    "https://github.com/advisories/GHSA-v626-r774-j7f8",
                    "https://github.com/tinymce/tinymce",
                    "https://github.com/tinymce/tinymce/releases/tag/5.10.9",
                    "https://github.com/tinymce/tinymce/releases/tag/6.7.3",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-v626-r774-j7f8",
                    "https://nvd.nist.gov/vuln/detail/CVE-2023-48219",
                    "https://tiny.cloud/docs/release-notes/release-notes5109/",
                    "https://tiny.cloud/docs/tinymce/6/6.7.3-release-notes/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "5.11.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-38356"
                    ],
                    "githubID": "GHSA-9hcv-j9pv-qmph",
                    "summary": "TinyMCE Cross-Site Scripting (XSS) vulnerability using noneditable_regexp option"
                },
                "info": [
                    "https://github.com/advisories/GHSA-9hcv-j9pv-qmph",
                    "https://github.com/tinymce/tinymce",
                    "https://github.com/tinymce/tinymce/commit/5acb741665a98e83d62b91713c800abbff43b00d",
                    "https://github.com/tinymce/tinymce/commit/a9fb858509f86dacfa8b01cfd34653b408983ac0",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-9hcv-j9pv-qmph",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-38356",
                    "https://owasp.org/www-community/attacks/xss",
                    "https://www.tiny.cloud/docs/tinymce/6/6.8.4-release-notes/#overview",
                    "https://www.tiny.cloud/docs/tinymce/7/7.2-release-notes/#overview",
                    "https://www.tiny.cloud/docs/tinymce/latest/7.2-release-notes/#overview"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "5.11.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-38357"
                    ],
                    "githubID": "GHSA-w9jx-4g6g-rp7x",
                    "summary": "TinyMCE Cross-Site Scripting (XSS) vulnerability using noscript elements"
                },
                "info": [
                    "https://github.com/advisories/GHSA-w9jx-4g6g-rp7x",
                    "https://github.com/tinymce/tinymce",
                    "https://github.com/tinymce/tinymce/commit/5acb741665a98e83d62b91713c800abbff43b00d",
                    "https://github.com/tinymce/tinymce/commit/a9fb858509f86dacfa8b01cfd34653b408983ac0",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-w9jx-4g6g-rp7x",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-38357",
                    "https://owasp.org/www-community/attacks/xss",
                    "https://www.tiny.cloud/docs/tinymce/6/6.8.4-release-notes/#overview",
                    "https://www.tiny.cloud/docs/tinymce/7/7.2-release-notes/#overview"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "6.0.0",
                "below": "6.3.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-23494"
                    ],
                    "githubID": "GHSA-gg8r-xjwq-4w92",
                    "summary": "A cross-site scripting (XSS) vulnerability in TinyMCE alerts which allowed arbitrary JavaScript execution was found and fixed."
                },
                "info": [
                    "https://github.com/advisories/GHSA-gg8r-xjwq-4w92",
                    "https://www.cve.org/CVERecord?id=CVE-2022-23494",
                    "https://www.tiny.cloud/docs/changelog/#5107-2022-12-06"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "6.0.0",
                "below": "6.7.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-45819"
                    ],
                    "githubID": "GHSA-hgqx-r2hp-jr38",
                    "summary": "TinyMCE XSS vulnerability in notificationManager.open API"
                },
                "info": [
                    "https://github.com/advisories/GHSA-hgqx-r2hp-jr38",
                    "https://www.cve.org/CVERecord?id=CVE-2022-23494",
                    "https://www.tiny.cloud/docs/changelog/#5107-2022-12-06"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "6.0.0",
                "below": "6.7.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-45818"
                    ],
                    "githubID": "GHSA-v65r-p3vv-jjfv",
                    "summary": "TinyMCE mXSS vulnerability in undo/redo, getContent API, resetContent API, and Autosave plugin"
                },
                "info": [
                    "https://github.com/advisories/GHSA-v65r-p3vv-jjfv"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "6.0.0",
                "below": "6.7.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2023-48219"
                    ],
                    "githubID": "GHSA-v626-r774-j7f8",
                    "summary": "TinyMCE vulnerable to mutation Cross-site Scripting via special characters in unescaped text nodes"
                },
                "info": [
                    "https://github.com/advisories/GHSA-v626-r774-j7f8",
                    "https://github.com/tinymce/tinymce",
                    "https://github.com/tinymce/tinymce/releases/tag/5.10.9",
                    "https://github.com/tinymce/tinymce/releases/tag/6.7.3",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-v626-r774-j7f8",
                    "https://nvd.nist.gov/vuln/detail/CVE-2023-48219",
                    "https://tiny.cloud/docs/release-notes/release-notes5109/",
                    "https://tiny.cloud/docs/tinymce/6/6.7.3-release-notes/"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "6.8.1",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-29203"
                    ],
                    "githubID": "GHSA-438c-3975-5x3f",
                    "summary": "TinyMCE Cross-Site Scripting (XSS) vulnerability in handling iframes"
                },
                "info": [
                    "https://github.com/advisories/GHSA-438c-3975-5x3f",
                    "https://github.com/tinymce/tinymce",
                    "https://github.com/tinymce/tinymce/commit/bcdea2ad14e3c2cea40743fb48c63bba067ae6d1",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-438c-3975-5x3f",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-29203",
                    "https://www.tiny.cloud/docs/tinymce/6/6.8.1-release-notes/#new-convert_unsafe_embeds-option-that-controls-whether-object-and-embed-elements-will-be-converted-to-more-restrictive-alternatives-namely-img-for-image-mime-types-video-for-video-mime-types-audio-audio-mime-types-or-iframe-for-other-or-unspecified-mime-types",
                    "https://www.tiny.cloud/docs/tinymce/7/7.0-release-notes/#sandbox_iframes-editor-option-is-now-defaulted-to-true"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "6.0.0",
                "below": "6.8.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-38356"
                    ],
                    "githubID": "GHSA-9hcv-j9pv-qmph",
                    "summary": "TinyMCE Cross-Site Scripting (XSS) vulnerability using noneditable_regexp option"
                },
                "info": [
                    "https://github.com/advisories/GHSA-9hcv-j9pv-qmph",
                    "https://github.com/tinymce/tinymce",
                    "https://github.com/tinymce/tinymce/commit/5acb741665a98e83d62b91713c800abbff43b00d",
                    "https://github.com/tinymce/tinymce/commit/a9fb858509f86dacfa8b01cfd34653b408983ac0",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-9hcv-j9pv-qmph",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-38356",
                    "https://owasp.org/www-community/attacks/xss",
                    "https://www.tiny.cloud/docs/tinymce/6/6.8.4-release-notes/#overview",
                    "https://www.tiny.cloud/docs/tinymce/7/7.2-release-notes/#overview",
                    "https://www.tiny.cloud/docs/tinymce/latest/7.2-release-notes/#overview"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "6.0.0",
                "below": "6.8.4",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-38357"
                    ],
                    "githubID": "GHSA-w9jx-4g6g-rp7x",
                    "summary": "TinyMCE Cross-Site Scripting (XSS) vulnerability using noscript elements"
                },
                "info": [
                    "https://github.com/advisories/GHSA-w9jx-4g6g-rp7x",
                    "https://github.com/tinymce/tinymce",
                    "https://github.com/tinymce/tinymce/commit/5acb741665a98e83d62b91713c800abbff43b00d",
                    "https://github.com/tinymce/tinymce/commit/a9fb858509f86dacfa8b01cfd34653b408983ac0",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-w9jx-4g6g-rp7x",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-38357",
                    "https://owasp.org/www-community/attacks/xss",
                    "https://www.tiny.cloud/docs/tinymce/6/6.8.4-release-notes/#overview",
                    "https://www.tiny.cloud/docs/tinymce/7/7.2-release-notes/#overview"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "0",
                "below": "7.0.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-29881"
                    ],
                    "githubID": "GHSA-5359-pvf2-pw78",
                    "summary": "TinyMCE Cross-Site Scripting (XSS) vulnerability in handling external SVG files through Object or Embed elements"
                },
                "info": [
                    "https://github.com/advisories/GHSA-5359-pvf2-pw78",
                    "https://github.com/tinymce/tinymce",
                    "https://github.com/tinymce/tinymce/commit/bcdea2ad14e3c2cea40743fb48c63bba067ae6d1",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-5359-pvf2-pw78",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-29881",
                    "https://www.tiny.cloud/docs/tinymce/6/6.8.1-release-notes/#new-convert_unsafe_embeds-option-that-controls-whether-object-and-embed-elements-will-be-converted-to-more-restrictive-alternatives-namely-img-for-image-mime-types-video-for-video-mime-types-audio-audio-mime-types-or-iframe-for-other-or-unspecified-mime-types",
                    "https://www.tiny.cloud/docs/tinymce/7/7.0-release-notes/#convert_unsafe_embeds-editor-option-is-now-defaulted-to-true"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "7.0.0",
                "below": "7.2.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-38356"
                    ],
                    "githubID": "GHSA-9hcv-j9pv-qmph",
                    "summary": "TinyMCE Cross-Site Scripting (XSS) vulnerability using noneditable_regexp option"
                },
                "info": [
                    "https://github.com/advisories/GHSA-9hcv-j9pv-qmph",
                    "https://github.com/tinymce/tinymce",
                    "https://github.com/tinymce/tinymce/commit/5acb741665a98e83d62b91713c800abbff43b00d",
                    "https://github.com/tinymce/tinymce/commit/a9fb858509f86dacfa8b01cfd34653b408983ac0",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-9hcv-j9pv-qmph",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-38356",
                    "https://owasp.org/www-community/attacks/xss",
                    "https://www.tiny.cloud/docs/tinymce/6/6.8.4-release-notes/#overview",
                    "https://www.tiny.cloud/docs/tinymce/7/7.2-release-notes/#overview",
                    "https://www.tiny.cloud/docs/tinymce/latest/7.2-release-notes/#overview"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "7.0.0",
                "below": "7.2.0",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-38357"
                    ],
                    "githubID": "GHSA-w9jx-4g6g-rp7x",
                    "summary": "TinyMCE Cross-Site Scripting (XSS) vulnerability using noscript elements"
                },
                "info": [
                    "https://github.com/advisories/GHSA-w9jx-4g6g-rp7x",
                    "https://github.com/tinymce/tinymce",
                    "https://github.com/tinymce/tinymce/commit/5acb741665a98e83d62b91713c800abbff43b00d",
                    "https://github.com/tinymce/tinymce/commit/a9fb858509f86dacfa8b01cfd34653b408983ac0",
                    "https://github.com/tinymce/tinymce/security/advisories/GHSA-w9jx-4g6g-rp7x",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-38357",
                    "https://owasp.org/www-community/attacks/xss",
                    "https://www.tiny.cloud/docs/tinymce/6/6.8.4-release-notes/#overview",
                    "https://www.tiny.cloud/docs/tinymce/7/7.2-release-notes/#overview"
                ],
                "severity": "medium"
            }
        ]
    },
    "ua-parser-js": {
        "extractors": {
            "filecontent": [
                ".=\"([0-9][0-9.a-z_-]+)\",.=\"\",.=\"\\?\",.=\"function\",.=\"undefined\",.=\"object\",(.=\"string\",)?.=\"major\",.=\"model\",.=\"name\",.=\"type\",.=\"vendor\"",
                ".\\.VERSION=\"([0-9][0-9.a-z_-]+)\",.\\.BROWSER=.\\(\\[[^\\]]{1,20}\\]\\),.\\.CPU=",
                ".\\.VERSION=\"([0-9][0-9.a-z_-]+)\",.\\.BROWSER=\\{NAME:.,MAJOR:\"major\",VERSION:.\\},.\\.CPU=\\{ARCHITECTURE:",
                "// UAParser.js v([0-9][0-9.a-z_-]+)",
                "/\\* UAParser.js v([0-9][0-9.a-z_-]+)",
                "/\\*[*!](?:@license)?[\\s]+\\* UAParser.js v([0-9][0-9.a-z_-]+)",
                "LIBVERSION=\"([0-9][0-9.a-z_-]+)\",EMPTY=\"\",UNKNOWN=\"\\?\",FUNC_TYPE=\"function\",UNDEF_TYPE=\"undefined\""
            ],
            "func": [
                "UAParser.VERSION",
                "$.ua.version"
            ],
            "uri": [
                "/([0-9][0-9.a-z_-]+)/ua-parser(.min)?.js"
            ]
        },
        "vulnerabilities": [
            {
                "atOrAbove": "0",
                "below": "0.7.22",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-7733"
                    ],
                    "githubID": "GHSA-662x-fhqg-9p8v",
                    "summary": "Regular Expression Denial of Service in ua-parser-js"
                },
                "info": [
                    "https://github.com/advisories/GHSA-662x-fhqg-9p8v",
                    "https://github.com/faisalman/ua-parser-js/commit/233d3bae22a795153a7e6638887ce159c63e557d",
                    "https://nvd.nist.gov/vuln/detail/CVE-2020-7733",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSBOWERGITHUBFAISALMAN-674666",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSNPM-674665",
                    "https://snyk.io/vuln/SNYK-JS-UAPARSERJS-610226",
                    "https://www.oracle.com//security-alerts/cpujul2021.html"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0",
                "below": "0.7.22",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-7733"
                    ],
                    "githubID": "GHSA-662x-fhqg-9p8v",
                    "summary": "Regular Expression Denial of Service in ua-parser-js"
                },
                "info": [
                    "https://github.com/advisories/GHSA-662x-fhqg-9p8v",
                    "https://github.com/faisalman/ua-parser-js/commit/233d3bae22a795153a7e6638887ce159c63e557d",
                    "https://nvd.nist.gov/vuln/detail/CVE-2020-7733",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSBOWERGITHUBFAISALMAN-674666",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSNPM-674665",
                    "https://snyk.io/vuln/SNYK-JS-UAPARSERJS-610226",
                    "https://www.oracle.com//security-alerts/cpujul2021.html"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0",
                "below": "0.7.23",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2020-7793"
                    ],
                    "githubID": "GHSA-394c-5j6w-4xmx",
                    "summary": "ua-parser-js Regular Expression Denial of Service vulnerability"
                },
                "info": [
                    "https://cert-portal.siemens.com/productcert/pdf/ssa-637483.pdf",
                    "https://github.com/advisories/GHSA-394c-5j6w-4xmx",
                    "https://github.com/faisalman/ua-parser-js/commit/6d1f26df051ba681463ef109d36c9cf0f7e32b18",
                    "https://nvd.nist.gov/vuln/detail/CVE-2020-7793",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSBOWERGITHUBFAISALMAN-1050388",
                    "https://snyk.io/vuln/SNYK-JAVA-ORGWEBJARSNPM-1050387",
                    "https://snyk.io/vuln/SNYK-JS-UAPARSERJS-1023599"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0.7.14",
                "below": "0.7.24",
                "cwe": [
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-27292"
                    ],
                    "githubID": "GHSA-78cj-fxph-m83p",
                    "summary": "Regular Expression Denial of Service (ReDoS) in ua-parser-js"
                },
                "info": [
                    "https://gist.github.com/b-c-ds/6941d80d6b4e694df4bc269493b7be76",
                    "https://github.com/advisories/GHSA-78cj-fxph-m83p",
                    "https://github.com/faisalman/ua-parser-js/commit/809439e20e273ce0d25c1d04e111dcf6011eb566",
                    "https://github.com/pygments/pygments/commit/2e7e8c4a7b318f4032493773732754e418279a14",
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-27292"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0.7.29",
                "below": "0.7.30",
                "cwe": [
                    "CWE-829",
                    "CWE-912"
                ],
                "identifiers": {
                    "CVE": [],
                    "githubID": "GHSA-pjwm-rvh2-c87w",
                    "summary": "Embedded malware in ua-parser-js"
                },
                "info": [
                    "https://github.com/advisories/GHSA-pjwm-rvh2-c87w",
                    "https://github.com/faisalman/ua-parser-js",
                    "https://github.com/faisalman/ua-parser-js/issues/536",
                    "https://github.com/faisalman/ua-parser-js/issues/536#issuecomment-949772496",
                    "https://www.npmjs.com/package/ua-parser-js"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0",
                "below": "0.7.33",
                "cwe": [
                    "CWE-1333",
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-25927"
                    ],
                    "githubID": "GHSA-fhg7-m89q-25r3",
                    "summary": "ReDoS Vulnerability in ua-parser-js version"
                },
                "info": [
                    "https://github.com/advisories/GHSA-fhg7-m89q-25r3",
                    "https://github.com/faisalman/ua-parser-js",
                    "https://github.com/faisalman/ua-parser-js/commit/a6140a17dd0300a35cfc9cff999545f267889411",
                    "https://github.com/faisalman/ua-parser-js/security/advisories/GHSA-fhg7-m89q-25r3",
                    "https://nvd.nist.gov/vuln/detail/CVE-2022-25927",
                    "https://security.snyk.io/vuln/SNYK-JS-UAPARSERJS-3244450"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0.8.0",
                "below": "0.8.1",
                "cwe": [
                    "CWE-829",
                    "CWE-912"
                ],
                "identifiers": {
                    "CVE": [],
                    "githubID": "GHSA-pjwm-rvh2-c87w",
                    "summary": "Embedded malware in ua-parser-js"
                },
                "info": [
                    "https://github.com/advisories/GHSA-pjwm-rvh2-c87w",
                    "https://github.com/faisalman/ua-parser-js",
                    "https://github.com/faisalman/ua-parser-js/issues/536",
                    "https://github.com/faisalman/ua-parser-js/issues/536#issuecomment-949772496",
                    "https://www.npmjs.com/package/ua-parser-js"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "1.0.0",
                "below": "1.0.1",
                "cwe": [
                    "CWE-829",
                    "CWE-912"
                ],
                "identifiers": {
                    "CVE": [],
                    "githubID": "GHSA-pjwm-rvh2-c87w",
                    "summary": "Embedded malware in ua-parser-js"
                },
                "info": [
                    "https://github.com/advisories/GHSA-pjwm-rvh2-c87w",
                    "https://github.com/faisalman/ua-parser-js",
                    "https://github.com/faisalman/ua-parser-js/issues/536",
                    "https://github.com/faisalman/ua-parser-js/issues/536#issuecomment-949772496",
                    "https://www.npmjs.com/package/ua-parser-js"
                ],
                "severity": "high"
            },
            {
                "atOrAbove": "0.8.0",
                "below": "1.0.33",
                "cwe": [
                    "CWE-1333",
                    "CWE-400"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2022-25927"
                    ],
                    "githubID": "GHSA-fhg7-m89q-25r3",
                    "summary": "ReDoS Vulnerability in ua-parser-js version"
                },
                "info": [
                    "https://github.com/advisories/GHSA-fhg7-m89q-25r3",
                    "https://github.com/faisalman/ua-parser-js",
                    "https://github.com/faisalman/ua-parser-js/commit/a6140a17dd0300a35cfc9cff999545f267889411",
                    "https://github.com/faisalman/ua-parser-js/security/advisories/GHSA-fhg7-m89q-25r3",
                    "https://nvd.nist.gov/vuln/detail/CVE-2022-25927",
                    "https://security.snyk.io/vuln/SNYK-JS-UAPARSERJS-3244450"
                ],
                "severity": "high"
            }
        ]
    },
    "underscore.js": {
        "bowername": [
            "Underscore",
            "underscore"
        ],
        "extractors": {
            "filecontent": [
                "// *Underscore\\.js[\\s\\S]{1,2500}_\\.VERSION *= *['\"]([0-9][0-9.a-z_-]+)['\"]",
                "//[\\s]*Underscore.js ([0-9][0-9.a-z_-]+)"
            ],
            "func": [
                "underscore.version"
            ],
            "uri": [
                "/underscore\\.js/([0-9][0-9.a-z_-]+)/underscore(-min)?\\.js"
            ]
        },
        "npmname": "underscore",
        "vulnerabilities": [
            {
                "atOrAbove": "1.3.2",
                "below": "1.12.1",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2021-23358"
                    ],
                    "githubID": "GHSA-cf4h-3jhx-xvhq",
                    "summary": " vulnerable to Arbitrary Code Injection via the template function"
                },
                "info": [
                    "https://nvd.nist.gov/vuln/detail/CVE-2021-23358"
                ],
                "severity": "high"
            }
        ]
    },
    "vue": {
        "extractors": {
            "filecontent": [
                "\"([0-9][0-9.a-z_-]+)\"[\\s\\S]{0,150}\\.createPolicy\\(\"vue\"",
                "'([0-9][0-9.a-z_-]+)'[^\\n]{0,8000}Vue compiler",
                "/\\*!\\n \\* Vue.js v([0-9][0-9.a-z_-]+)",
                "/\\*\\*?!?\\n ?\\* vue v([0-9][0-9.a-z_-]+)",
                "Vue.version = '([0-9][0-9.a-z_-]+)';",
                "\\* Original file: /npm/vue@([0-9][0-9.a-z_-]+)/dist/vue.(global|common).js",
                "\\.__vue_app__=.{0,8000}?const [a-z]+=\"([0-9][0-9.a-z_-]+)\",",
                "const version[ ]*=[ ]*\"([0-9][0-9.a-z_-]+)\";[\\s]*/\\*\\*[\\s]*\\* SSR utils for \\\\@vue/server-renderer",
                "devtoolsFormatters[\\s\\S]{50,180}\"([0-9][0-9.a-z_-]+)\"[\\s\\S]{50,180}\\.createElement\\(\"template\"\\)",
                "isCustomElement.{1,5}?compilerOptions.{0,500}exposeProxy.{0,700}\"([0-9][0-9.a-z_-]+)\"",
                "let [A-Za-z]+=\"([0-9][0-9.a-z_-]+)\",..=\"undefined\"!=typeof window&&window.trustedTypes;if\\(..\\)try\\{.=..\\.createPolicy\\(\"vue\","
            ],
            "filename": [
                "vue-([0-9][0-9.a-z_-]+)(\\.min)?\\.js"
            ],
            "func": [
                "Vue.version"
            ],
            "uri": [
                "/npm/vue@([0-9][0-9.a-z_-]+)",
                "/vue/([0-9][0-9.a-z_-]+)/vue\\..*\\.js",
                "/vue@([0-9][0-9.a-z_-]+)/dist/vue\\.js"
            ]
        },
        "vulnerabilities": [
            {
                "below": "2.4.3",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "12",
                    "summary": "possible xss vector"
                },
                "info": [
                    "https://github.com/vuejs/vue/releases/tag/v2.4.3"
                ],
                "severity": "medium"
            },
            {
                "below": "2.5.17",
                "cwe": [
                    "CWE-79"
                ],
                "identifiers": {
                    "retid": "11",
                    "summary": "potential xss in ssr when using v-bind"
                },
                "info": [
                    "https://github.com/vuejs/vue/releases/tag/v2.5.17"
                ],
                "severity": "medium"
            },
            {
                "below": "2.6.11",
                "cwe": [
                    "CWE-94"
                ],
                "identifiers": {
                    "retid": "10",
                    "summary": "Bump vue-server-renderer's dependency of serialize-javascript to 2.1.2"
                },
                "info": [
                    "https://github.com/vuejs/vue/releases/tag/v2.6.11"
                ],
                "severity": "medium"
            },
            {
                "atOrAbove": "2.0.0-alpha.1",
                "below": "3.0.0-alpha.0",
                "cwe": [
                    "CWE-1333"
                ],
                "identifiers": {
                    "CVE": [
                        "CVE-2024-9506"
                    ],
                    "githubID": "GHSA-5j4c-8p2g-v4jx",
                    "summary": "ReDoS vulnerability in vue package that is exploitable through inefficient regex evaluation in the parseHTML function"
                },
                "info": [
                    "https://github.com/advisories/GHSA-5j4c-8p2g-v4jx",
                    "https://github.com/vuejs/core",
                    "https://nvd.nist.gov/vuln/detail/CVE-2024-9506",
                    "https://www.herodevs.com/vulnerability-directory/cve-2024-9506"
                ],
                "severity": "low"
            }
        ]
    }
}
