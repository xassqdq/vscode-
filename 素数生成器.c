/*
 素数生成器 - C 语言版 (命令行)
 功能：
 - 在区间内生成素数并追加到 ndjson 文件 `primes_db.ndjson`
 - 判断一个数是否为素数（Miller-Rabin）
 - 对输入整数做质因数分解（简单试除法）
 - 加载 / 清空素数库（ndjson）
 - 按固定区间统计素数个数并输出为 CSV（便于绘图）

 编译（Windows，MinGW 或类似支持 __int128 的编译器）：
 gcc -O2 -std=c99 -o 素数生成器 素数生成器.c -lm

 使用：运行可交互的菜单。
*/

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define PRIME_DB_ND "primes_db.ndjson"

/* ---------- 基本整型运算（防溢出） ---------- */
static uint64_t mul_mod(uint64_t a, uint64_t b, uint64_t mod) {
#ifdef __SIZEOF_INT128__
    return (uint64_t)((unsigned __int128)a * b % mod);
#else
    uint64_t res = 0;
    a %= mod;
    while (b) {
        if (b & 1) res = (res + a) % mod;
        a = (a * 2) % mod;
        b >>= 1;
    }
    return res;
#endif
}

static uint64_t pow_mod(uint64_t a, uint64_t d, uint64_t mod) {
    uint64_t res = 1;
    a %= mod;
    while (d) {
        if (d & 1) res = mul_mod(res, a, mod);
        a = mul_mod(a, a, mod);
        d >>= 1;
    }
    return res;
}

/* ---------- Miller-Rabin 确定性基集（适用于 64-bit） ---------- */
static int miller_rabin(uint64_t n) {
    if (n < 2) return 0;
    static const uint64_t small_primes[] = {2,3,5,7,11,13,17,19,23,29,31,37};
    for (size_t i = 0; i < sizeof(small_primes)/sizeof(small_primes[0]); ++i) {
        uint64_t p = small_primes[i];
        if (n == p) return 1;
        if (n % p == 0) return 0;
    }
    uint64_t d = n - 1;
    int s = 0;
    while ((d & 1) == 0) { d >>= 1; s++; }
    uint64_t bases[] = {2ULL, 325ULL, 9375ULL, 28178ULL, 450775ULL, 9780504ULL, 1795265022ULL};
    for (size_t i = 0; i < sizeof(bases)/sizeof(bases[0]); ++i) {
        uint64_t a = bases[i] % n;
        if (a == 0) continue;
        uint64_t x = pow_mod(a, d, n);
        if (x == 1 || x == n-1) continue;
        int composite = 1;
        for (int r = 1; r < s; ++r) {
            x = mul_mod(x, x, n);
            if (x == n-1) { composite = 0; break; }
        }
        if (composite) return 0;
    }
    return 1;
}

/* ---------- 简单埃拉托斯特尼筛（用于生成小素数） ---------- */
typedef struct { uint64_t *data; size_t size; size_t cap; } u64vec;
static void vec_init(u64vec *v) { v->data = NULL; v->size = 0; v->cap = 0; }
static void vec_push(u64vec *v, uint64_t x) {
    if (v->size == v->cap) { v->cap = v->cap ? v->cap * 2 : 256; v->data = realloc(v->data, v->cap * sizeof(uint64_t)); }
    v->data[v->size++] = x;
}
static void vec_free(u64vec *v) { free(v->data); v->data = NULL; v->size = v->cap = 0; }

static void sieve_primes_up_to(uint64_t limit, u64vec *out) {
    if (limit < 2) return;
    uint8_t *sieve = malloc((size_t)limit + 1);
    if (!sieve) return;
    memset(sieve, 1, (size_t)limit + 1);
    sieve[0] = sieve[1] = 0;
    for (uint64_t p = 2; p * p <= limit; ++p) {
        if (!sieve[p]) continue;
        for (uint64_t q = p * p; q <= limit; q += p) sieve[q] = 0;
    }
    for (uint64_t i = 2; i <= limit; ++i) if (sieve[i]) vec_push(out, i);
    free(sieve);
}

/* 分段筛：生成 [low, high] 区间内的素数并写入文件（追加） */
static int generate_primes_range(uint64_t low, uint64_t high, const char *out_file) {
    if (high < 2 || low > high) return 0;
    if (low < 2) low = 2;
    uint64_t limit = (uint64_t)sqrt((double)high) + 1;
    u64vec small; vec_init(&small); sieve_primes_up_to(limit, &small);
    uint64_t segment_size = 1 << 16; /* 65536 */
    uint64_t total = 0;
    FILE *f = fopen(out_file, "a");
    if (!f) { perror("打开输出文件失败"); vec_free(&small); return -1; }
    for (uint64_t low0 = low; low0 <= high; low0 += segment_size) {
        uint64_t high0 = low0 + segment_size - 1;
        if (high0 > high) high0 = high;
        uint64_t len = high0 - low0 + 1;
        uint8_t *isprime = malloc((size_t)len);
        if (!isprime) { fclose(f); vec_free(&small); return -1; }
        memset(isprime, 1, (size_t)len);
        for (size_t i = 0; i < small.size; ++i) {
            uint64_t p = small.data[i];
            uint64_t p2 = p * p;
            if (p2 > high0) break;
            uint64_t start = (low0 + p - 1) / p * p;
            if (start < p2) start = p2;
            for (uint64_t m = start; m <= high0; m += p) isprime[m - low0] = 0;
        }
        for (uint64_t i = 0; i < len; ++i) {
            if (isprime[i]) {
                uint64_t val = low0 + i;
                fprintf(f, "%" PRIu64 "\n", val);
                total++;
            }
        }
        free(isprime);
    }
    fclose(f);
    vec_free(&small);
    return (int)total;
}

/* 判定是否为素数（包装） */
static int is_prime_u64(uint64_t n) { return miller_rabin(n); }

/* 质因数分解（简单试除法，适合中小整数） */
static void prime_factors_u64(uint64_t n) {
    if (n <= 1) { printf("%" PRIu64 " 无质因数\n", n); return; }
    uint64_t orig = n;
    int printed = 0;
    for (uint64_t p = 2; p <= 3 && n > 1; ++p) {
        while (n % p == 0) {
            if (printed) printf(" × ");
            printf("%" PRIu64, p); printed = 1; n /= p;
        }
    }
    uint64_t f = 5;
    while (f * f <= n) {
        for (int k = 0; k < 2; ++k) {
            uint64_t p = f + k * 2;
            while (n % p == 0) {
                if (printed) printf(" × ");
                printf("%" PRIu64, p); printed = 1; n /= p;
            }
        }
        f += 6;
    }
    if (n > 1) {
        if (printed) printf(" × ");
        printf("%" PRIu64, n);
    }
    printf(" = %" PRIu64 "\n", orig);
}

/* 统计区间内每个小区间的素数数量（返回写入 CSV 所需的数据） */
static int count_primes_in_ranges(uint64_t start, uint64_t end, uint64_t interval, const char *out_csv) {
    if (end < 2 || start > end) return 0;
    if (start < 2) start = 2;
    FILE *f = NULL;
    if (out_csv) f = fopen(out_csv, "w");
    if (f) fprintf(f, "range,count\n");
    uint64_t limit = (uint64_t)sqrt((double)end) + 1;
    u64vec small; vec_init(&small); sieve_primes_up_to(limit, &small);
    uint64_t total_ranges = 0;
    for (uint64_t cur = start; cur <= end; cur += interval) {
        uint64_t nxt = cur + interval - 1;
        if (nxt > end) nxt = end;
        uint64_t cnt = 0;
        uint64_t seg_size = nxt - cur + 1;
        uint8_t *isprime = malloc((size_t)seg_size);
        if (!isprime) { vec_free(&small); if (f) fclose(f); return -1; }
        memset(isprime, 1, (size_t)seg_size);
        for (size_t i = 0; i < small.size; ++i) {
            uint64_t p = small.data[i];
            uint64_t p2 = p * p;
            if (p2 > nxt) break;
            uint64_t start_idx = (cur + p - 1) / p * p;
            if (start_idx < p2) start_idx = p2;
            for (uint64_t m = start_idx; m <= nxt; m += p) isprime[m - cur] = 0;
        }
        for (uint64_t i = 0; i < seg_size; ++i) if (isprime[i]) cnt++;
        if (f) fprintf(f, "%" PRIu64 "-%" PRIu64 ",%" PRIu64 "\n", cur, nxt, cnt);
        free(isprime);
        total_ranges++;
    }
    vec_free(&small);
    if (f) fclose(f);
    return (int)total_ranges;
}

/* 加载素数库（显示数量及前若干项） */
static void load_db_preview(const char *db_file) {
    FILE *f = fopen(db_file, "r");
    if (!f) { printf("未找到素数库：%s\n", db_file); return; }
    char line[128];
    uint64_t count = 0;
    uint64_t preview[50]; size_t pv = 0;
    while (fgets(line, sizeof(line), f)) {
        char *s = line;
        while (*s == ' ' || *s == '\t') s++;
        if (s[0] == '\n' || s[0] == '\0') continue;
        uint64_t v = strtoull(s, NULL, 10);
        if (pv < sizeof(preview)/sizeof(preview[0])) preview[pv++] = v;
        count++;
    }
    fclose(f);
    printf("素数库共 %" PRIu64 " 个素数。前 %zu 个：\n", count, pv);
    for (size_t i = 0; i < pv; ++i) {
        if (i) printf(", ");
        printf("%" PRIu64, preview[i]);
    }
    printf("\n");
}

static void clear_db(const char *db_file) {
    if (remove(db_file) == 0) printf("已删除 %s\n", db_file);
    else printf("未找到或无法删除 %s\n", db_file);
}

/* 交互菜单 */
int main(void) {
    while (1) {
        printf("\n===== 素数生成器 (C 版) =====\n");
        printf("1) 生成并保存区间素数 (追加到 %s)\n", PRIME_DB_ND);
        printf("2) 判断单个数字是否为素数并可追加到库\n");
        printf("3) 素数库预览与加载\n");
        printf("4) 清空素数库\n");
        printf("5) 统计区间分布并输出 CSV\n");
        printf("6) 退出\n");
        printf("请选择: ");
        int choice = 0; if (scanf("%d", &choice) != 1) { while (getchar()!='\n'); continue; }
        if (choice == 1) {
            unsigned long long a,b; printf("起始值: "); scanf("%llu", &a); printf("终止值: "); scanf("%llu", &b);
            if (b <= a) { printf("终止值必须大于起始值\n"); continue; }
            printf("开始生成 %llu 到 %llu 的素数并追加到 %s...\n", a, b, PRIME_DB_ND);
            int added = generate_primes_range((uint64_t)a, (uint64_t)b, PRIME_DB_ND);
            if (added >= 0) printf("已追加 %d 个素数\n", added);
        } else if (choice == 2) {
            unsigned long long x; printf("输入要判断的数字: "); scanf("%llu", &x);
            if (is_prime_u64((uint64_t)x)) {
                printf("%llu 是素数。\n", x);
                FILE *f = fopen(PRIME_DB_ND, "a"); if (f) { fprintf(f, "%" PRIu64 "\n", (uint64_t)x); fclose(f); }
            } else {
                printf("%llu 不是素数。质因数分解：\n", x);
                prime_factors_u64((uint64_t)x);
            }
        } else if (choice == 3) {
            load_db_preview(PRIME_DB_ND);
        } else if (choice == 4) {
            clear_db(PRIME_DB_ND);
        } else if (choice == 5) {
            unsigned long long s,e,interval; char csvname[256];
            printf("起始值: "); scanf("%llu", &s); printf("终止值: "); scanf("%llu", &e);
            printf("区间大小: "); scanf("%llu", &interval);
            printf("输出 CSV 文件名 (留空使用 distribution.csv): ");
            while (getchar()!='\n'); fgets(csvname, sizeof(csvname), stdin);
            if (csvname[0] == '\n' || csvname[0] == '\0') strcpy(csvname, "distribution.csv");
            else {
                char *p = strchr(csvname, '\n'); if (p) *p = '\0';
            }
            printf("统计并输出到 %s ...\n", csvname);
            int ranges = count_primes_in_ranges((uint64_t)s, (uint64_t)e, (uint64_t)interval, csvname);
            if (ranges >= 0) printf("已输出 %d 个区间的统计到 %s\n", ranges, csvname);
        } else if (choice == 6) {
            break;
        } else {
            printf("无效选择\n");
        }
    }
    return 0;
}