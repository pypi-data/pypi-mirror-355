#ifndef metkit_version_h
#define metkit_version_h

#define metkit_VERSION_STR "1.13.4.dev20250613"
#define metkit_VERSION     "1.13.4"

#define metkit_VERSION_MAJOR 1
#define metkit_VERSION_MINOR 13
#define metkit_VERSION_PATCH 4

#define metkit_GIT_SHA1 "2c4935114c2fc937b19edee1e6d0c08f1623e003"

#ifdef __cplusplus
extern "C" {
#endif

const char * metkit_version();

unsigned int metkit_version_int();

const char * metkit_version_str();

const char * metkit_git_sha1();

#ifdef __cplusplus
}
#endif


#endif // metkit_version_h
