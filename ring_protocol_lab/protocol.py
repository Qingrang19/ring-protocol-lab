"""Pure ring arithmetic; all externally visible electrode labels use index_base."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    electrodes: int = 16
    drive_step: int = 1
    index_base: int = 0

    def __post_init__(self):
        for name in ('electrodes', 'drive_step', 'index_base'):
            if type(getattr(self, name)) is not int:
                raise ValueError(f'{name} must be an integer')
        if not 4 <= self.electrodes <= 512:
            raise ValueError('electrodes must be between 4 and 512')
        if not 1 <= self.drive_step < self.electrodes:
            raise ValueError('drive_step must be between 1 and electrodes - 1')
        if self.index_base not in (0, 1):
            raise ValueError('index_base must be 0 or 1')
        if self.electrodes == 4 and self.drive_step == 2:
            raise ValueError('4-electrode opposite drive leaves no adjacent measurements')


def generate(config):
    """Produce ordered current and voltage pairs; preserve reverse excitations."""
    n, step, base = config.electrodes, config.drive_step, config.index_base
    rows = []
    for excitation in range(n):
        drive = (excitation, (excitation + step) % n)
        for start in range(n):
            measurement = (start, (start + 1) % n)
            if set(drive).isdisjoint(measurement):
                rows.append(dict(excitation=excitation + base,
                                 drive_plus=drive[0] + base, drive_minus=drive[1] + base,
                                 measure_plus=measurement[0] + base,
                                 measure_minus=measurement[1] + base))
    return rows


FIELDS = ('excitation', 'drive_plus', 'drive_minus', 'measure_plus', 'measure_minus')


def validate(rows, config):
    """Require the complete canonical table, including order and polarity."""
    if not isinstance(rows, list):
        raise ValueError('rows must be a list')
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != set(FIELDS):
            raise ValueError(f'row {i}: expected fields {", ".join(FIELDS)}')
        if any(type(row[key]) is not int for key in FIELDS):
            raise ValueError(f'row {i}: all fields must be integers')
    expected = generate(config)
    if len(rows) != len(expected):
        raise ValueError(f'expected {len(expected)} rows, got {len(rows)}')
    for i, (actual, wanted) in enumerate(zip(rows, expected)):
        if actual != wanted:
            raise ValueError(f'row {i}: does not match the configured canonical protocol')
    return len(rows)
