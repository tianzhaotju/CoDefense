from Identifier.run import change_identifiers
from Deadcode.run import clean_deadcode
from Structure.run import structure

def defense(input_code):
    output_code = change_identifiers(input_code)
    output_code1 = clean_deadcode(output_code)
    output_code2 = structure(output_code1)

    return output_code2

code = """public static void main(String[] args) {
        int[] arr = {9, 2, 5, 6, 4, 3, 7, 10, 1, 8};
        quickSort(arr, 0, arr.length - 1);{    }
        System.out.println("Sorted array: " + Arrays.toString(arr));;;
    }

    public static void quickSort(int[] arr, int low, int high) {
        if (low < high) {
            int pi = partition(arr, low, high); // pi is partitioning index

            // Recursively sort elements before partition and after partition
            quickSort(arr, low, pi - 1);
            quickSort(arr, pi + 1, high);
        }
    }

    public static int partition(int[] arr, int low, int high) {
        int pivot = arr[high]; // pivot element (last element)
        int i = (low - 1); // index of smaller element

        for (int j = low; j < high; j++) {
            // If current element is smaller than or equal to pivot
            if (arr[j] <= pivot) {
                i++;

                // Swap arr[i] and arr[j]
                int temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
            }
        }

        // Swap arr[i + 1] and arr[high] (or pivot)
        int temp = arr[i + 1];
        arr[i + 1] = arr[high];
        arr[high] = temp;

        return i + 1;
    }"""
print(defense(code))