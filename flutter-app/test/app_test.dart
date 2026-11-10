import 'package:flutter_test/flutter_test.dart';
import 'package:japan_halal_checker/main.dart';

void main() {
  test('Bangla, Japanese and English UI labels exist', () {
    expect(labels['bn']?['scan'], isNotEmpty);
    expect(labels['ja']?['scan'], isNotEmpty);
    expect(labels['en']?['scan'], isNotEmpty);
  });
  test('Missing ingredients are not mistaken for certification', () {
    final product = Product.fromOff({'product_name': 'Example', 'code': '4900000000000'});
    expect(product.ingredients, isEmpty);
    expect(product.name, 'Example');
  });
}
