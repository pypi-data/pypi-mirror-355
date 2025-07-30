from typing import Union


class BaseClass:

    def __init__(self):
        self.random_index = 10

    def summ_index(self, index: Union[int, str]) -> int:

        if isinstance(index, str):
            try:
                return int(index) + self.random_index
            except ValueError as err:
                return f"Не смогли просуммировать из-за ошибки {err}"

        if not isinstance(index, int):
            raise ValueError(
                f"Некорректное значение переданной перменной. Нужно int, имеем {type(index)}."
            )

        return index + self.random_index


if __name__ == "__main__":

    my_class = BaseClass()

    print(my_class.summ_index("5"))
