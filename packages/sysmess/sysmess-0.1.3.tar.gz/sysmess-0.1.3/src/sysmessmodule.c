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
#define BOX_UL_ROUND "\xE2\x95\xAD"
#define BOX_UR_ROUND "\xE2\x95\xAE"
#define BOX_LL_ROUND "\xE2\x95\xB0"
#define BOX_LR_ROUND "\xE2\x95\xAF"
#define ANSI_BOLD "\x1b[1m"
#define ANSI_ITALIC "\x1b[3m"
#define ANSI_RESET "\x1b[0m"

static const char *
get_ansi_color(const char *name)
{
    if (!name) {
        return NULL;
    }
    if (strcmp(name, "black") == 0) return "\x1b[30m";
    else if (strcmp(name, "red") == 0) return "\x1b[31m";
    else if (strcmp(name, "green") == 0) return "\x1b[32m";
    else if (strcmp(name, "yellow") == 0) return "\x1b[33m";
    else if (strcmp(name, "blue") == 0) return "\x1b[34m";
    else if (strcmp(name, "magenta") == 0) return "\x1b[35m";
    else if (strcmp(name, "cyan") == 0) return "\x1b[36m";
    else if (strcmp(name, "white") == 0) return "\x1b[37m";
    else if (strcmp(name, "bright_black") == 0) return "\x1b[90m";
    else if (strcmp(name, "bright_red") == 0) return "\x1b[91m";
    else if (strcmp(name, "bright_green") == 0) return "\x1b[92m";
    else if (strcmp(name, "bright_yellow") == 0) return "\x1b[93m";
    else if (strcmp(name, "bright_blue") == 0) return "\x1b[94m";
    else if (strcmp(name, "bright_magenta") == 0) return "\x1b[95m";
    else if (strcmp(name, "bright_cyan") == 0) return "\x1b[96m";
    else if (strcmp(name, "bright_white") == 0) return "\x1b[97m";
    return NULL;
}

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
    static char *kwlist[] = {
        "message", "title", "center", "bold", "italic", "style",
        "border_color", "title_color", "body_color", NULL
    };
    PyObject *msg_obj;
    PyObject *title_obj = NULL;
    int center = 0, bold = 0, italic = 0;
    const char *style_name = NULL;
    const char *border_color = NULL, *title_color = NULL, *body_color = NULL;
    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, "U|Upppzzzz", kwlist,
            &msg_obj, &title_obj, &center, &bold, &italic, &style_name,
            &border_color, &title_color, &body_color)) {
        return NULL;
    }

    const char *border_ansi = get_ansi_color(border_color);
    if (border_color && !border_ansi) {
        PyErr_Format(PyExc_ValueError,
                     "Invalid border_color '%s'", border_color);
        return NULL;
    }
    const char *title_ansi = get_ansi_color(title_color);
    if (title_color && !title_ansi) {
        PyErr_Format(PyExc_ValueError,
                     "Invalid title_color '%s'", title_color);
        return NULL;
    }
    const char *body_ansi = get_ansi_color(body_color);
    if (body_color && !body_ansi) {
        PyErr_Format(PyExc_ValueError,
                     "Invalid body_color '%s'", body_color);
        return NULL;
    }
    int round_corners = 0;
    if (style_name) {
        if (strcmp(style_name, "round") == 0) {
            round_corners = 1;
        } else {
            PyErr_Format(PyExc_ValueError,
                         "Invalid style '%s'", style_name);
            return NULL;
        }
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
    const char *ul = round_corners ? BOX_UL_ROUND : BOX_UL;
    const char *ur = round_corners ? BOX_UR_ROUND : BOX_UR;
    const char *ll = round_corners ? BOX_LL_ROUND : BOX_LL;
    const char *lr = round_corners ? BOX_LR_ROUND : BOX_LR;
    if (border_ansi) ds_append_str(&ds, border_ansi);
    ds_append_str(&ds, ul);
    ds_append_n(&ds, BOX_HOR, inner);
    ds_append_str(&ds, ur);
    if (border_ansi) ds_append_str(&ds, ANSI_RESET);
    ds_append_str(&ds, "\n");
    if (title_obj) {
        const char *tutf = PyUnicode_AsUTF8(title_obj);
        Py_ssize_t tlen = PyUnicode_GetLength(title_obj);
        if (border_ansi) ds_append_str(&ds, border_ansi);
        ds_append_str(&ds, BOX_VER);
        if (border_ansi) ds_append_str(&ds, ANSI_RESET);
        ds_append_str(&ds, " ");
        if (bold) ds_append_str(&ds, ANSI_BOLD);
        if (italic) ds_append_str(&ds, ANSI_ITALIC);
        if (title_ansi) ds_append_str(&ds, title_ansi);
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
        if (bold || italic || title_ansi) ds_append_str(&ds, ANSI_RESET);
        ds_append_str(&ds, " ");
        if (border_ansi) ds_append_str(&ds, border_ansi);
        ds_append_str(&ds, BOX_VER);
        if (border_ansi) ds_append_str(&ds, ANSI_RESET);
        ds_append_str(&ds, "\n");
        if (border_ansi) ds_append_str(&ds, border_ansi);
        ds_append_str(&ds, BOX_TSEP_L);
        ds_append_n(&ds, BOX_HOR, inner);
        ds_append_str(&ds, BOX_TSEP_R);
        if (border_ansi) ds_append_str(&ds, ANSI_RESET);
        ds_append_str(&ds, "\n");
    }
    for (Py_ssize_t i = 0; i < count; i++) {
        PyObject *line = PyList_GetItem(lines, i);
        const char *lutf = PyUnicode_AsUTF8(line);
        Py_ssize_t llen = PyUnicode_GetLength(line);
        if (border_ansi) ds_append_str(&ds, border_ansi);
        ds_append_str(&ds, BOX_VER);
        if (border_ansi) ds_append_str(&ds, ANSI_RESET);
        ds_append_str(&ds, " ");
        if (bold) ds_append_str(&ds, ANSI_BOLD);
        if (italic) ds_append_str(&ds, ANSI_ITALIC);
        if (body_ansi) ds_append_str(&ds, body_ansi);
        ds_append_str(&ds, lutf);
        if (bold || italic || body_ansi) ds_append_str(&ds, ANSI_RESET);
        ds_append_str(&ds, " ");
        for (Py_ssize_t j = 0; j < maxlen - llen; j++) ds_append_str(&ds, " ");
        if (border_ansi) ds_append_str(&ds, border_ansi);
        ds_append_str(&ds, BOX_VER);
        if (border_ansi) ds_append_str(&ds, ANSI_RESET);
        ds_append_str(&ds, "\n");
    }
    Py_DECREF(lines);
    if (border_ansi) ds_append_str(&ds, border_ansi);
    ds_append_str(&ds, ll);
    ds_append_n(&ds, BOX_HOR, inner);
    ds_append_str(&ds, lr);
    if (border_ansi) ds_append_str(&ds, ANSI_RESET);
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
     PyDoc_STR(
         "fancy_box(message, title=None, center=False, bold=False, italic=False,"
         " style=None, border_color=None, title_color=None, body_color=None) -> str\n"
         "Return a string with the message enclosed in a fancy box. "
         "Optionally specify style='round' for rounded corners. "
         "Colors can be specified for the border, title and body using basic color names: "
         "black, red, green, yellow, blue, magenta, cyan, white, bright_black, bright_red, "
         "bright_green, bright_yellow, bright_blue, bright_magenta, bright_cyan, bright_white."
     )},
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