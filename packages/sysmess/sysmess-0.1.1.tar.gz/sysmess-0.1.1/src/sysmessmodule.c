#include <Python.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char *buf;
    size_t len;
    size_t cap;
} DynamicString;

static int ds_ensure(DynamicString *ds, size_t add) {
    if (ds->len + add + 1 > ds->cap) {
        size_t newcap = ds->cap * 2;
        while (newcap <= ds->len + add) {
            newcap *= 2;
        }
        char *nb = PyMem_Realloc(ds->buf, newcap);
        if (!nb) {
            return -1;
        }
        ds->buf = nb;
        ds->cap = newcap;
    }
    return 0;
}

static int ds_init(DynamicString *ds) {
    ds->cap = 128;
    ds->len = 0;
    ds->buf = PyMem_Malloc(ds->cap);
    if (!ds->buf) {
        return -1;
    }
    ds->buf[0] = '\0';
    return 0;
}

static void ds_free(DynamicString *ds) {
    PyMem_Free(ds->buf);
}

static int ds_append(DynamicString *ds, const char *s, size_t n) {
    if (ds_ensure(ds, n) < 0) {
        return -1;
    }
    memcpy(ds->buf + ds->len, s, n);
    ds->len += n;
    ds->buf[ds->len] = '\0';
    return 0;
}

static int ds_append_str(DynamicString *ds, const char *s) {
    return ds_append(ds, s, strlen(s));
}

static int ds_append_n(DynamicString *ds, const char *s, size_t n) {
    size_t slen = strlen(s);
    size_t total = slen * n;
    if (ds_ensure(ds, total) < 0) {
        return -1;
    }
    for (size_t i = 0; i < n; i++) {
        memcpy(ds->buf + ds->len + i * slen, s, slen);
    }
    ds->len += total;
    ds->buf[ds->len] = '\0';
    return 0;
}

#define BOX_UL "\xE2\x94\x8C"
#define BOX_UR "\xE2\x94\x90"
#define BOX_LL "\xE2\x94\x94"
#define BOX_LR "\xE2\x94\x98"
#define BOX_HOR "\xE2\x94\x80"
#define BOX_VER "\xE2\x94\x82"
#define BOX_TSEP_L "\xE2\x94\x9C"
#define BOX_TSEP_R "\xE2\x94\xA4"
#define ANSI_BOLD "\x1b[1m"
#define ANSI_ITALIC "\x1b[3m"
#define ANSI_RESET "\x1b[0m"

static PyObject *
sysmess_measure_box_width(PyObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {"message", "title", NULL};
    PyObject *msg_obj;
    PyObject *title_obj = NULL;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "U|U", kwlist,
                                     &msg_obj, &title_obj)) {
        return NULL;
    }
    PyObject *lines = PyObject_CallMethod(msg_obj, "splitlines", NULL);
    if (!lines) {
        return NULL;
    }
    Py_ssize_t maxlen = 0;
    Py_ssize_t count = PyList_Size(lines);
    for (Py_ssize_t i = 0; i < count; i++) {
        PyObject *line = PyList_GetItem(lines, i);
        Py_ssize_t llen = PyUnicode_GetLength(line);
        if (llen > maxlen) {
            maxlen = llen;
        }
    }
    if (title_obj) {
        Py_ssize_t tlen = PyUnicode_GetLength(title_obj);
        if (tlen > maxlen) {
            maxlen = tlen;
        }
    }
    Py_DECREF(lines);
    Py_ssize_t width = maxlen + 4;
    return PyLong_FromSsize_t(width);
}

static PyObject *
sysmess_fancy_box(PyObject *self, PyObject *args, PyObject *kwargs)
{
    static char *kwlist[] = {"message", "title", "center", "bold", "italic", NULL};
    PyObject *msg_obj;
    PyObject *title_obj = NULL;
    int center = 0, bold = 0, italic = 0;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "U|Uppp", kwlist,
                                     &msg_obj, &title_obj,
                                     &center, &bold, &italic)) {
        return NULL;
    }
    PyObject *lines = PyObject_CallMethod(msg_obj, "splitlines", NULL);
    if (!lines) {
        return NULL;
    }
    Py_ssize_t maxlen = 0;
    Py_ssize_t count = PyList_Size(lines);
    for (Py_ssize_t i = 0; i < count; i++) {
        PyObject *line = PyList_GetItem(lines, i);
        Py_ssize_t llen = PyUnicode_GetLength(line);
        if (llen > maxlen) {
            maxlen = llen;
        }
    }
    if (title_obj) {
        Py_ssize_t tlen = PyUnicode_GetLength(title_obj);
        if (tlen > maxlen) {
            maxlen = tlen;
        }
    }
    Py_ssize_t inner = maxlen + 2;
    DynamicString ds;
    if (ds_init(&ds) < 0) {
        Py_DECREF(lines);
        return PyErr_NoMemory();
    }
    ds_append_str(&ds, BOX_UL);
    ds_append_n(&ds, BOX_HOR, inner);
    ds_append_str(&ds, BOX_UR);
    ds_append_str(&ds, "\n");
    if (title_obj) {
        const char *tutf = PyUnicode_AsUTF8(title_obj);
        Py_ssize_t tlen = PyUnicode_GetLength(title_obj);
        ds_append_str(&ds, BOX_VER);
        ds_append_str(&ds, " ");
        if (bold) ds_append_str(&ds, ANSI_BOLD);
        if (italic) ds_append_str(&ds, ANSI_ITALIC);
        if (center) {
            Py_ssize_t pad = maxlen - tlen;
            Py_ssize_t left = pad/2;
            Py_ssize_t right = pad - left;
            for (Py_ssize_t i = 0; i < left; i++) ds_append_str(&ds, " ");
            ds_append_str(&ds, tutf);
            for (Py_ssize_t i = 0; i < right; i++) ds_append_str(&ds, " ");
        } else {
            ds_append_str(&ds, tutf);
            for (Py_ssize_t i = 0; i < maxlen - tlen; i++) ds_append_str(&ds, " ");
        }
        if (bold || italic) ds_append_str(&ds, ANSI_RESET);
        ds_append_str(&ds, " ");
        ds_append_str(&ds, BOX_VER);
        ds_append_str(&ds, "\n");
        ds_append_str(&ds, BOX_TSEP_L);
        ds_append_n(&ds, BOX_HOR, inner);
        ds_append_str(&ds, BOX_TSEP_R);
        ds_append_str(&ds, "\n");
    }
    for (Py_ssize_t i = 0; i < count; i++) {
        PyObject *line = PyList_GetItem(lines, i);
        const char *lutf = PyUnicode_AsUTF8(line);
        Py_ssize_t llen = PyUnicode_GetLength(line);
        ds_append_str(&ds, BOX_VER);
        ds_append_str(&ds, " ");
        if (bold) ds_append_str(&ds, ANSI_BOLD);
        if (italic) ds_append_str(&ds, ANSI_ITALIC);
        ds_append_str(&ds, lutf);
        if (bold || italic) ds_append_str(&ds, ANSI_RESET);
        ds_append_str(&ds, " ");
        for (Py_ssize_t j = 0; j < maxlen - llen; j++) ds_append_str(&ds, " ");
        ds_append_str(&ds, BOX_VER);
        ds_append_str(&ds, "\n");
    }
    Py_DECREF(lines);
    ds_append_str(&ds, BOX_LL);
    ds_append_n(&ds, BOX_HOR, inner);
    ds_append_str(&ds, BOX_LR);
    ds_append_str(&ds, "\n");
    PyObject *result = PyUnicode_DecodeUTF8(ds.buf, ds.len, NULL);
    ds_free(&ds);
    return result;
}

static PyMethodDef SysmessMethods[] = {
    {"measure_box_width", (PyCFunction)sysmess_measure_box_width,
     METH_VARARGS | METH_KEYWORDS,
     PyDoc_STR("measure_box_width(message, title=None) -> int\n"
               "Return the total width of the box including borders.")},
    {"fancy_box", (PyCFunction)sysmess_fancy_box,
     METH_VARARGS | METH_KEYWORDS,
     PyDoc_STR("fancy_box(message, title=None, center=False, bold=False, italic=False) -> str\n"
               "Return a string with the message enclosed in a fancy box.")},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef sysmessmodule = {
    PyModuleDef_HEAD_INIT,
    "sysmess",
    NULL,
    -1,
    SysmessMethods
};

PyMODINIT_FUNC PyInit_sysmess(void) {
    return PyModule_Create(&sysmessmodule);
}