

class RegressionFeatures(StatsTransformer):
    def __init__(
        self,
        rule: Types.Quadrants | Tuple[Types.Quadrants],
        deviation: None | int | Tuple[int, ...] = None,
        **kwargs,
    ):
        """
        Docs are used in code.
        :param rule: must be either
            1) quadrants (Tuple[int]), direction to classify
               regressions, 1st quadrant being upper-right square of plane and counting
               anti-clockwise,
            2) tuple of quadrants (Tuple[Tuple[int]]), each value in tuple defines a separate feature, same as
               creating multiple RegressionFeatures with different `rule` values as in 1)
            3) tuple of angles in degrees (0 <= angle <= 360), analogous to 1) byt with angles
               instead of quadrants.
            4) tuple of tuple of angles in degrees (0 <= angle <= 360), analogous to 2) but
               with angles instead of quadrants.
               Angle = 0 is positive x-axis direction, rotating anti-clockwise.
        :param deviation: if
            a) None, then `rule` is interpreted as 1) or 2);
            b) integer, then is a +-deviation for all angles and `rule` is interpreted as 3) or 4);
            c) tuple of integers, then is a +-deviation for corresponding angles and `rule` is interpreted as 3);
            d) tuple of tuple of integers, then `rule` is interpreted as 4).
        """
        super().__init__(**kwargs)
        self.available_feats = ("length", "acceleration", "speed", "mask")
        self.rule = rule
        self.deviation = deviation
        self.is_angle = None

    @property
    def _fp(self) -> str:
        return "reg"

    def _check_params(self):
        # check `rule`
        if (                                             # 1) or 3)
                isinstance(self.rule, tuple) and
                [isinstance(q, int) for q in self.rule]
        ):
            rule_option = {1, 3}
        elif (
                isinstance(self.rule, tuple) and
                [isinstance(q, int) for r in self.rule for q in r]
        ):                                               # 2) or 4)
            rule_option = {2, 4}
        else:
            raise ValueError("Wrong type for `rule` parameter.")

        if isinstance(self.rule[0], int):
            self.rule = (self.rule,)  # Tuple[Tuple[int]]

        # check `deviation`
        if self.deviation is None:                         # a)
            deviation_option = {1, 2}
            self.deviation = (None for _ in range(len(self.rule)))

        elif isinstance(self.deviation, int):              # b)
            deviation_option = {3, 4}
            assert 0 <= self.deviation <= 180,\
                f"Deviation must be 0 <= deviation <= 180, got {self.deviation}."
            self.deviation = (self.deviation for _ in range(len(self.rule)))

        elif (                                             # c)
                isinstance(self.deviation, tuple) and
                [isinstance(d, int) for d in self.deviation]
        ):
            deviation_option = {3}
            for d in self.deviation:
                assert 0 <= d <= 180, \
                    f"Deviation must be 0 <= deviation <= 180, got {d}."
            assert len(self.deviation) == len(self.rule)

        elif (                                             # d)
                isinstance(self.deviation, tuple) and
                [isinstance(d, int) for r in self.deviation for d in r]
        ):
            deviation_option = {4}
            assert 4 in rule_option
            assert len(self.deviation) == len(self.rule)
            for i in range(len(self.rule)):
                assert len(self.deviation[i]) == len(self.rule[i])

        else:
            raise ValueError("Wrong type for `deviation` parameter.")

        option = rule_option.intersection(deviation_option)
        if len(option) == 0:
            raise RuntimeError("Wrong combination of `rule` and `deviation` parameters,"
                               "refer to docs for and example.")

        assert len(option) == 1
        option = list(option)[0]

        self.is_angle = option in (1, 3)

        if not self.is_angle:
            for r in self.rule:
                for q in r:
                    assert q in (1, 2, 3, 4), f"Wrong quadrant {q} in `rule`."

        else:
            for r in self.rule:
                for a in r:
                    assert 0 <= a <= 360, f"Angles must be 0 <= angle <= 360, got {a}."

        for feat in self.feature_names_in:
            assert self.x is not None, self._err_no_col(feat, "x")
            assert self.y is not None, self._err_no_col(feat, "y")
            if feat in ("speed", "acceleration"):
                assert self.t is not None
                self._err_no_col(feat, "t")

    def _calc_feats(
        self, X: pd.DataFrame, features: List[str], transition_mask: NDArray
    ) -> List[Tuple[str, pd.Series]]:
        feats = []

        dx: pd.Series = X[self.x].diff()
        dy: pd.Series = X[self.y].diff()
        sm = _select_regressions(dx, dy, self.rule, self.deviation)  # selection_mask
        dr = np.sqrt(dx**2 + dy**2)
        dt = None

        tm = transition_mask[sm]
        if "length" in features:
            sac_len = dr
            feats.append(("length", sac_len[sm][tm]))
        if "acceleration" in features:
            # Acceleration: dx = v0 * t + 1/2 * a * t^2.
            # Above formula is law of uniformly accelerated motion TODO consider direction
            dt = _calc_dt(X, self.duration, self.t)
            sac_acc: pd.DataFrame = dr / (dt**2 + self.eps) * 1 / 2
            feats.append(("acceleration", sac_acc[sm][tm]))
        if "speed" in features:
            dt = dt if dt is not None else _calc_dt(X, self.duration, self.t)
            sac_spd = dr / (dt + self.eps)
            feats.append(("speed", sac_spd[sm][tm]))
        if "mask" in features:
            feats.append(("mask", sm))

        return feats
