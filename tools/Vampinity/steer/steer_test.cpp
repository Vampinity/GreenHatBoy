// Host test of minimap_steer.h: drawn minimaps for the directions, and a small world in which
// Link runs where the stick and the camera say, to see the walk reach its points.
//   c++ -std=c++20 -Wall -Wextra -Werror -I <path to headless/> steer_test.cpp -o steer_test && ./steer_test
#include <cmath>
#include <cstdio>
#include <utility>
#include <vector>
#include "minimap_steer.h"

static int failed = 0;
#define CHECK(what) do { if (!(what)) { std::printf("FAIL line %d: %s\n", __LINE__, #what); ++failed; } } while (0)

static const double kPi = 3.14159265358979323846;

// A 1280 x 720 picture with a minimap drawn into its region: a yellow map, Link's red arrowhead
// at (x, y) of the picture in pixels and the camera's pale wedge toward `camera` degrees.
struct Drawn {
    unsigned width = 1280, height = 720;
    std::vector<unsigned char> bgra = std::vector<unsigned char>(1280 * 720 * 4, 20);
    void Put(int x, int y, int r, int g, int b) {
        if (x < 0 || y < 0 || x >= static_cast<int>(width) || y >= static_cast<int>(height)) return;
        unsigned char* p = bgra.data() + (static_cast<std::size_t>(y) * width + x) * 4;
        p[0] = static_cast<unsigned char>(b), p[1] = static_cast<unsigned char>(g), p[2] = static_cast<unsigned char>(r), p[3] = 255;
    }
    void Map() {  // a yellow disc in the middle of the region
        for (int y = 560; y < 700; ++y)
            for (int x = 1000; x < 1220; ++x)
                if (std::hypot(x - 1110.0, (y - 630.0) * 1.4) < 105) Put(x, y, 230, 200, 60);
    }
    void Icon(int x, int y) {  // an orange map icon the size of the arrowhead: not Link
        for (int dy = -4; dy <= 4; ++dy)
            for (int dx = -4; dx <= 4; ++dx) Put(x + dx, y + dy, 235, 140, 60);
    }
    void Link(double x, double y, double camera, bool wedge = true) {
        if (wedge) {
            for (int dy = -34; dy <= 34; ++dy)
                for (int dx = -34; dx <= 34; ++dx) {
                    const double distance = std::hypot(dx, dy);
                    if (distance < 2 || distance > 34) continue;
                    double angle = std::atan2(dx, -dy) * 180 / kPi;
                    const double off = std::fabs(std::remainder(angle - camera, 360.0));
                    if (off <= 32) Put(static_cast<int>(x) + dx, static_cast<int>(y) + dy, 250, 250, 215);
                }
        }
        for (int dy = -3; dy <= 3; ++dy)
            for (int dx = -3; dx <= 3; ++dx) Put(static_cast<int>(x) + dx, static_cast<int>(y) + dy, 190, 25, 30);
    }
    steer::Fix Find(bool flip = false) const { return steer::Find(bgra.data(), width, height, flip); }
};

static double Milli(double pixel, double size) { return pixel * 1000.0 / size; }

static void Directions() {
    for (double camera : {0.0, 45.0, 90.0, 180.0, 270.0, 333.0}) {
        Drawn picture;
        picture.Map();
        picture.Icon(1080, 610);
        picture.Link(1130, 640, camera);
        const steer::Fix fix = picture.Find();
        CHECK(fix.map && fix.found && fix.view);
        CHECK(std::fabs(fix.x - Milli(1130, 1280)) < 1.0 && std::fabs(fix.y - Milli(640, 720)) < 1.5);
        CHECK(std::fabs(std::remainder(fix.angle - camera, 360.0)) < 6.0);
    }
    // The stick: up is where the camera looks.
    Drawn picture;
    picture.Map();
    picture.Link(1130, 640, 0);  // the camera looks up the map (north)
    steer::Fix fix = picture.Find();
    steer::Stick stick = steer::Toward(fix, fix.x, fix.y - 30);  // a point to the north
    CHECK(stick.y < 8 && std::abs(stick.x - 128) < 12);          // stick up
    stick = steer::Toward(fix, fix.x + 30, fix.y);               // east
    CHECK(stick.x > 247 && std::abs(stick.y - 128) < 12);        // stick right
    stick = steer::Toward(fix, fix.x, fix.y + 30);               // south
    CHECK(stick.y > 247);                                        // stick down: toward the camera
    Drawn east;
    east.Map();
    east.Link(1130, 640, 90);  // the camera looks east
    fix = east.Find();
    stick = steer::Toward(fix, fix.x, fix.y - 30);               // north is on the camera's left
    CHECK(stick.x < 8 && std::abs(stick.y - 128) < 12);
    stick = steer::Toward(fix, fix.x + 30, fix.y);               // east is straight ahead
    CHECK(stick.y < 8);
    // The same picture stored bottom row first reads the same.
    Drawn flipped = east;
    for (unsigned row = 0; row < flipped.height / 2; ++row)
        std::swap_ranges(flipped.bgra.begin() + row * flipped.width * 4, flipped.bgra.begin() + (row + 1) * flipped.width * 4,
                         flipped.bgra.begin() + (flipped.height - 1 - row) * flipped.width * 4);
    const steer::Fix other = flipped.Find(true);
    CHECK(other.found && std::fabs(other.x - fix.x) < 0.01 && std::fabs(other.y - fix.y) < 0.01 &&
          std::fabs(other.angle - fix.angle) < 0.01);
}

static void NotLink() {
    Drawn none;  // no map: a dark screen
    CHECK(!none.Find().map && !none.Find().found);
    Drawn icon;  // a map with only the orange icon
    icon.Map();
    icon.Icon(1080, 610);
    CHECK(icon.Find().map && !icon.Find().view);
    Drawn no_wedge;  // the arrowhead without its wedge: found, but nothing to steer by
    no_wedge.Map();
    no_wedge.Link(1130, 640, 0, false);
    const steer::Fix fix = no_wedge.Find();
    CHECK(fix.found && !fix.view);
    const steer::Stick stick = steer::Toward(fix, fix.x + 30, fix.y);
    CHECK(stick.x == 128 && stick.y == 128);
    Drawn red_screen;  // a screen that is red all over is not an arrowhead
    for (int y = 0; y < 720; ++y)
        for (int x = 0; x < 1280; ++x) red_screen.Put(x, y, 200, 20, 20);
    CHECK(!red_screen.Find().found);
    unsigned char tiny[4] = {};
    CHECK(!steer::Find(tiny, 1, 1, false).map);
    CHECK(!steer::Find(nullptr, 1280, 720, false).map);
    // Twice the size, the same answer (the grid is the same whatever the picture's size).
    Drawn small;
    small.Map();
    small.Link(1130, 640, 120);
    std::vector<unsigned char> big(2560 * 1440 * 4);
    for (unsigned y = 0; y < 1440; ++y)
        for (unsigned x = 0; x < 2560; ++x)
            for (int c = 0; c < 4; ++c)
                big[(static_cast<std::size_t>(y) * 2560 + x) * 4 + c] = small.bgra[(static_cast<std::size_t>(y / 2) * 1280 + x / 2) * 4 + c];
    const steer::Fix a = small.Find(), b = steer::Find(big.data(), 2560, 1440, false);
    // within a pixel of the small picture: the region's corner is rounded to a whole pixel of each
    CHECK(b.found && b.view && std::fabs(a.x - b.x) < 1.0 && std::fabs(a.y - b.y) < 1.0 && std::fabs(a.angle - b.angle) < 2);
}

// A small world: Link runs at `speed` pixels a second where the stick points relative to the
// camera, and the camera swings behind him at `turn` degrees a second. Looks come every 0.5 s and
// arrive one look late, as the app's do. Returns the seconds the walk took, or -1 on a timeout.
static double Walked(std::vector<std::pair<unsigned, unsigned>> points, double x, double y, double camera, double speed,
                     double turn, double timeout, int blind_from = -1, int blind_looks = 0) {
    steer::Walk walk;
    steer::Stick stick;
    bool holding = false;
    int looks = 0;
    for (double t = 0; t < timeout; t += 0.05) {
        if (std::fmod(t, 0.5) < 0.05) {
            Drawn picture;
            picture.Map();
            const bool blind = blind_from >= 0 && looks >= blind_from && looks < blind_from + blind_looks;
            if (!blind) picture.Link(x, y, camera);
            ++looks;
            steer::Stick next;
            const auto todo = walk.Look(picture.Find(), points, 6, 4, next);
            if (todo == steer::Walk::Do::Done) return t;
            if (todo == steer::Walk::Do::Hold) stick = next, holding = true;
            if (todo == steer::Walk::Do::Stand) holding = false;
        }
        if (!holding) continue;
        const double aside = (stick.x - 128) / 127.0, ahead = (128 - stick.y) / 127.0;
        if (std::hypot(aside, ahead) < 0.2) continue;
        const double radians = camera * kPi / 180;
        const double move_x = ahead * std::sin(radians) + aside * std::cos(radians);
        const double move_y = -ahead * std::cos(radians) + aside * std::sin(radians);
        x += move_x * speed * 0.05;
        y += move_y * speed * 0.05;
        const double heading = std::atan2(move_x, -move_y) * 180 / kPi;
        const double off = std::remainder(heading - camera, 360.0);
        camera += std::clamp(off, -turn * 0.05, turn * 0.05);
    }
    return -1;
}

static void Walks() {
    const auto milli = [](double px, double py) {
        return std::pair<unsigned, unsigned>{static_cast<unsigned>(std::lround(Milli(px, 1280))),
                                             static_cast<unsigned>(std::lround(Milli(py, 720)))};
    };
    // A loop of four points on the map, 6 px/s (Link's speed on the minimap in the recordings).
    const std::vector<std::pair<unsigned, unsigned>> loop{milli(1150, 600), milli(1170, 650), milli(1090, 660), milli(1070, 610)};
    for (double camera : {0.0, 90.0, 180.0, 270.0}) {   // whichever way the camera looks at the start
        for (double turn : {0.0, 40.0, 200.0}) {         // a camera that never turns, a slow one, a quick one
            const double took = Walked(loop, 1075, 615, camera, 6.0, turn, 120);
            CHECK(took > 0);
            CHECK(took < 75);  // the loop is about 245 px: 41 s at 6 px/s, with room for the corners
        }
    }
    // Ten looks without the marker in the middle (a talk, a fade): he stands, then goes on.
    const double with_gap = Walked(loop, 1075, 615, 0, 6.0, 40, 120, 20, 10);
    CHECK(with_gap > 0 && with_gap < 85);
    // A point that cannot be reached in time: a timeout, not a walk that never ends.
    CHECK(Walked({milli(1150, 600)}, 1075, 615, 0, 0.5, 40, 20) < 0);
    // A walk that starts on its first point passes it at the first look.
    steer::Walk walk;
    steer::Stick stick;
    Drawn at;
    at.Map();
    at.Link(1150, 600, 0);
    CHECK(walk.Look(at.Find(), std::vector<std::pair<unsigned, unsigned>>{milli(1150, 600)}, 6, 4, stick) == steer::Walk::Do::Done);
    // Lost looks: keep, keep, keep, then stand.
    steer::Walk lost;
    Drawn nothing;
    for (int i = 0; i < 3; ++i) CHECK(lost.Look(nothing.Find(), loop, 6, 4, stick) == steer::Walk::Do::Keep);
    CHECK(lost.Look(nothing.Find(), loop, 6, 4, stick) == steer::Walk::Do::Stand);
}

int main() {
    Directions();
    NotLink();
    Walks();
    std::puts(failed ? "FAILED" : "minimap steer: directions, not-Link cases, walks in a small world PASS");
    return failed ? 1 : 0;
}
