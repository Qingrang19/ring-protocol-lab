"""Dependency-free SVG schematic, intentionally not a physical field model."""
import math
from .protocol import generate


def render(config, excitation):
    base, n = config.index_base, config.electrodes
    if type(excitation) is not int or not base <= excitation < base + n:
        raise ValueError(f'excitation must be between {base} and {base + n - 1}')
    rows = [r for r in generate(config) if r['excitation'] == excitation]
    points = {i + base: (300 + 215 * math.cos(2 * math.pi * i / n - math.pi / 2),
                         290 + 215 * math.sin(2 * math.pi * i / n - math.pi / 2))
              for i in range(n)}
    drive = (excitation, (excitation - base + config.drive_step) % n + base)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="600" height="620" viewBox="0 0 600 620" role="img">',
             f'<title>Ring protocol: excitation {excitation}, {n} electrodes</title>',
             '<rect width="600" height="620" fill="#0b1728"/>',
             '<circle cx="300" cy="290" r="215" fill="none" stroke="#52647e" stroke-width="2"/>']
    def line(a, b, color, width):
        x1, y1 = points[a]; x2, y2 = points[b]
        return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}"/>'
    for row in rows:
        parts.append(line(row['measure_plus'], row['measure_minus'], '#4de1c0', 5))
    parts.append(line(*drive, '#ffb85c', 4))
    for label, (x, y) in points.items():
        color = '#ffb85c' if label in drive else '#dce8f8'
        parts += [f'<circle cx="{x:.2f}" cy="{y:.2f}" r="7" fill="{color}"/>',
                  f'<text x="{300 + (x-300)*1.12:.2f}" y="{294 + (y-290)*1.12:.2f}" text-anchor="middle" fill="{color}" font-family="monospace" font-size="12">{label}</text>']
    parts += [f'<text x="30" y="565" fill="#ffb85c" font-family="monospace" font-size="16">Drive +{drive[0]} / -{drive[1]}</text>',
              f'<text x="30" y="592" fill="#4de1c0" font-family="monospace" font-size="14">{len(rows)} adjacent voltage pairs; clockwise + to -</text>', '</svg>']
    return '\n'.join(parts) + '\n'
