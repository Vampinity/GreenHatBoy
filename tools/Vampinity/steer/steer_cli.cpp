// Runs minimap_steer.h over raw frames: steer_cli WIDTH HEIGHT [to_x to_y] < frames.bgra
// One line per frame: index map found view x y angle area [stick_x stick_y]. For tests and for
// steer-route.py; never part of the app.
// Build: c++ -std=c++20 -O2 -I <path to headless/> steer_cli.cpp -o steer-cli
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "minimap_steer.h"
int main(int argc, char** argv) {
    if (argc < 3) return 2;
    const unsigned width = static_cast<unsigned>(std::atoi(argv[1])), height = static_cast<unsigned>(std::atoi(argv[2]));
    const bool aim = argc >= 5;
    const double to_x = aim ? std::atof(argv[3]) : 0, to_y = aim ? std::atof(argv[4]) : 0;
    std::vector<unsigned char> frame(std::size_t{width} * height * 4);
    for (unsigned index = 0; std::fread(frame.data(), 1, frame.size(), stdin) == frame.size(); ++index) {
        const steer::Fix fix = steer::Find(frame.data(), width, height, false);
        std::printf("%u %d %d %d %.1f %.1f %.1f %d", index, fix.map, fix.found, fix.view, fix.x, fix.y, fix.angle, fix.area);
        if (aim) {
            const steer::Stick stick = steer::Toward(fix, to_x, to_y);
            std::printf(" %u %u", stick.x, stick.y);
        }
        std::printf("\n");
    }
    return 0;
}
