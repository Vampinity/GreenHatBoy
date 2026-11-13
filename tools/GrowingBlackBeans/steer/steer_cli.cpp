// SPDX-License-Identifier: GPL-3.0-or-later
// steer_cli: run the harness's own minimap finder (minimap_steer.h, unchanged) over raw frames.
//
//   ffmpeg -i walk.mp4 -vf fps=4 -f rawvideo -pix_fmt bgra - | steer_cli WIDTH HEIGHT FPS
//
// One line per frame on stdout: "t map found view x y angle area", t in seconds from the first frame,
// x and y in per mille of the picture, angle in degrees (0 = up, clockwise). The same numbers the
// console's STEER sees, because it is the same code: nothing here re-implements Find.
#include "minimap_steer.h"
#include <cstdio>
#include <cstdlib>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 4) {
        std::fprintf(stderr, "usage: steer_cli WIDTH HEIGHT FPS < raw bgra frames\n");
        return 2;
    }
    const unsigned width = static_cast<unsigned>(std::atoi(argv[1]));
    const unsigned height = static_cast<unsigned>(std::atoi(argv[2]));
    const double fps = std::atof(argv[3]);
    if (width == 0 || height == 0 || fps <= 0) return 2;
    std::vector<unsigned char> frame(static_cast<std::size_t>(width) * height * 4);
    for (unsigned long n = 0;; ++n) {
        if (std::fread(frame.data(), 1, frame.size(), stdin) != frame.size()) break;
        const steer::Fix f = steer::Find(frame.data(), width, height, false);
        std::printf("%.3f %d %d %d %.2f %.2f %.1f %d\n", n / fps, f.map, f.found, f.view, f.x, f.y,
                    f.angle, f.area);
    }
    return 0;
}
